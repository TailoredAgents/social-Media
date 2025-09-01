"""
Personality-Driven Response Engine for Social Media Interactions

Generates contextual, brand-aligned responses using company knowledge base
and configurable personality settings for Facebook, Instagram, and X.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.db.models import (
    SocialInteraction, ResponseTemplate, CompanyKnowledge, 
    InteractionResponse, User, UserSetting
)
from backend.db.database import get_db
from backend.agents.tools import openai_tool

logger = logging.getLogger(__name__)


class PersonalityResponseEngine:
    """
    AI-powered response engine that generates personality-aligned responses
    to social media interactions using company knowledge base.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.personality_styles = {
            "professional": {
                "tone": "formal and courteous",
                "language": "business-appropriate",
                "emoji_usage": "minimal",
                "response_length": "comprehensive"
            },
            "friendly": {
                "tone": "warm and approachable", 
                "language": "conversational",
                "emoji_usage": "moderate",
                "response_length": "concise but personal"
            },
            "casual": {
                "tone": "relaxed and informal",
                "language": "everyday speech",
                "emoji_usage": "frequent",
                "response_length": "brief and punchy"
            },
            "technical": {
                "tone": "informative and precise",
                "language": "industry terminology",
                "emoji_usage": "rare",
                "response_length": "detailed and thorough"
            }
        }
    
    def analyze_interaction_intent(self, content: str) -> Dict[str, Any]:
        """
        Analyze interaction content to determine intent, sentiment, and priority.
        
        Args:
            content: The interaction content to analyze
            
        Returns:
            Dictionary containing intent, sentiment, priority_score, and keywords
        """
        try:
            # Use AI to analyze the interaction
            analysis_prompt = f"""
            Analyze this social media interaction and provide:
            1. Intent (question, complaint, praise, lead, spam, general)
            2. Sentiment (positive, negative, neutral)
            3. Priority score (0-100, where 100 is highest priority)
            4. Key topics/keywords mentioned
            5. Urgency level (low, medium, high)
            
            Interaction content: "{content}"
            
            Respond in JSON format:
            {{
                "intent": "question",
                "sentiment": "neutral", 
                "priority_score": 50,
                "keywords": ["keyword1", "keyword2"],
                "urgency": "medium",
                "reasoning": "Brief explanation of the analysis"
            }}
            """
            
            response = openai_tool(analysis_prompt, temperature=0.3)
            
            # Parse JSON response
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # Fallback to simple keyword-based analysis
                analysis = self._fallback_content_analysis(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return self._fallback_content_analysis(content)
    
    def _fallback_content_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback analysis using keyword matching"""
        content_lower = content.lower()
        
        # Simple intent detection
        if any(word in content_lower for word in ["?", "how", "what", "when", "where", "why"]):
            intent = "question"
            priority_score = 70
        elif any(word in content_lower for word in ["problem", "issue", "broken", "error", "complaint"]):
            intent = "complaint"
            priority_score = 85
        elif any(word in content_lower for word in ["great", "awesome", "love", "amazing", "fantastic"]):
            intent = "praise" 
            priority_score = 30
        elif any(word in content_lower for word in ["buy", "purchase", "price", "cost", "interested"]):
            intent = "lead"
            priority_score = 90
        else:
            intent = "general"
            priority_score = 40
        
        # Simple sentiment detection
        positive_words = ["good", "great", "love", "awesome", "amazing", "excellent"]
        negative_words = ["bad", "terrible", "hate", "awful", "horrible", "worst"]
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "intent": intent,
            "sentiment": sentiment,
            "priority_score": priority_score,
            "keywords": [],
            "urgency": "medium",
            "reasoning": "Fallback keyword-based analysis"
        }
    
    def search_company_knowledge(
        self, 
        user_id: int, 
        query_keywords: List[str], 
        context_type: str = "general"
    ) -> List[CompanyKnowledge]:
        """
        Search company knowledge base for relevant information.
        
        Args:
            user_id: User ID to search knowledge for
            query_keywords: Keywords to search for
            context_type: Type of context (customer_service, sales, etc.)
            
        Returns:
            List of relevant knowledge entries
        """
        try:
            # Start with exact keyword matches
            knowledge_entries = []
            
            for keyword in query_keywords:
                if not keyword.strip():
                    continue
                    
                # Search in title, content, keywords, and tags
                entries = self.db.query(CompanyKnowledge).filter(
                    CompanyKnowledge.user_id == user_id,
                    CompanyKnowledge.is_active == True,
                    (
                        CompanyKnowledge.title.ilike(f"%{keyword}%") |
                        CompanyKnowledge.content.ilike(f"%{keyword}%") |
                        CompanyKnowledge.keywords.op('@>')([keyword]) |
                        CompanyKnowledge.tags.op('@>')([keyword])
                    )
                ).limit(3).all()
                
                knowledge_entries.extend(entries)
            
            # Remove duplicates and sort by usage count
            unique_entries = list({entry.id: entry for entry in knowledge_entries}.values())
            unique_entries.sort(key=lambda x: x.usage_count or 0, reverse=True)
            
            return unique_entries[:5]  # Return top 5 most relevant
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    def find_matching_template(
        self, 
        user_id: int, 
        intent: str, 
        platform: str, 
        keywords: List[str]
    ) -> Optional[ResponseTemplate]:
        """
        Find a matching response template based on intent and keywords.
        
        Args:
            user_id: User ID
            intent: Detected intent
            platform: Social media platform
            keywords: Content keywords
            
        Returns:
            Matching response template or None
        """
        try:
            # Look for templates that match the intent and platform
            templates = self.db.query(ResponseTemplate).filter(
                ResponseTemplate.user_id == user_id,
                ResponseTemplate.is_active == True,
                ResponseTemplate.trigger_type == intent,
                ResponseTemplate.platforms.op('@>')([platform])
            ).order_by(ResponseTemplate.priority.desc()).all()
            
            # Find template with matching keywords
            for template in templates:
                template_keywords = template.keywords or []
                if any(keyword.lower() in [tk.lower() for tk in template_keywords] for keyword in keywords):
                    return template
            
            # If no keyword match, return first template for the intent
            return templates[0] if templates else None
            
        except Exception as e:
            logger.error(f"Template search failed: {e}")
            return None
    
    def generate_personalized_response(
        self,
        interaction: SocialInteraction,
        analysis: Dict[str, Any],
        knowledge_entries: List[CompanyKnowledge],
        template: Optional[ResponseTemplate] = None,
        personality_style: str = "professional"
    ) -> Dict[str, Any]:
        """
        Generate a personalized response using AI based on context and personality.
        
        Args:
            interaction: The social interaction to respond to
            analysis: Content analysis results
            knowledge_entries: Relevant company knowledge
            template: Optional template to use
            personality_style: Personality style to apply
            
        Returns:
            Generated response with metadata
        """
        try:
            # Get personality settings
            personality = self.personality_styles.get(personality_style, self.personality_styles["professional"])
            
            # Build context for AI
            context = self._build_response_context(
                interaction, analysis, knowledge_entries, personality, template
            )
            
            # Generate response using AI
            response_prompt = f"""
            You are an AI assistant representing a company's social media account.
            Generate a response to this social media interaction based on the following context:
            
            INTERACTION DETAILS:
            Platform: {interaction.platform}
            Type: {interaction.interaction_type}
            Author: @{interaction.author_username}
            Content: "{interaction.content}"
            
            ANALYSIS:
            Intent: {analysis.get('intent', 'general')}
            Sentiment: {analysis.get('sentiment', 'neutral')}
            Priority: {analysis.get('priority_score', 50)}/100
            
            PERSONALITY STYLE: {personality_style}
            - Tone: {personality['tone']}
            - Language: {personality['language']}
            - Emoji usage: {personality['emoji_usage']}
            - Response length: {personality['response_length']}
            
            COMPANY KNOWLEDGE:
            {context['knowledge_context']}
            
            TEMPLATE (if available):
            {context['template_context']}
            
            REQUIREMENTS:
            1. Stay in character with the {personality_style} personality style
            2. Address the customer's {analysis.get('intent', 'concern')} appropriately
            3. Use company knowledge when relevant
            4. Keep response appropriate for {interaction.platform}
            5. Be helpful and maintain brand voice
            6. If it's a complaint, be empathetic and solution-focused
            7. If it's praise, be gracious and engaging
            8. If it's a question, be informative and helpful
            
            Generate ONLY the response text (no quotes or explanation):
            """
            
            response_text = openai_tool(response_prompt, temperature=0.7)
            
            # Clean up response
            response_text = self._clean_response_text(response_text, interaction.platform)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(analysis, knowledge_entries, template)
            
            return {
                "response_text": response_text,
                "confidence_score": confidence_score,
                "personality_style": personality_style,
                "template_used": template.id if template else None,
                "knowledge_sources": [entry.id for entry in knowledge_entries],
                "response_reasoning": f"Generated {personality_style} response for {analysis.get('intent', 'general')} intent"
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._generate_fallback_response(interaction, analysis, personality_style)
    
    def _build_response_context(
        self,
        interaction: SocialInteraction,
        analysis: Dict[str, Any],
        knowledge_entries: List[CompanyKnowledge],
        personality: Dict[str, str],
        template: Optional[ResponseTemplate]
    ) -> Dict[str, str]:
        """Build context string for AI response generation"""
        
        # Knowledge context
        if knowledge_entries:
            knowledge_context = "\n".join([
                f"- {entry.title}: {entry.summary or entry.content[:200]}"
                for entry in knowledge_entries
            ])
        else:
            knowledge_context = "No specific company knowledge found for this topic."
        
        # Template context  
        if template:
            template_context = f"""
            Template: {template.name}
            Template text: {template.response_text}
            Variables: {', '.join(template.variables or [])}
            """
        else:
            template_context = "No specific template found - generate original response."
        
        return {
            "knowledge_context": knowledge_context,
            "template_context": template_context
        }
    
    def _clean_response_text(self, response_text: str, platform: str) -> str:
        """Clean and format response text for specific platform"""
        
        # Remove quotes if AI added them
        response_text = response_text.strip().strip('"\'')
        
        # Platform-specific formatting
        if platform == "twitter":
            # Ensure Twitter character limit
            if len(response_text) > 280:
                response_text = response_text[:277] + "..."
        elif platform == "instagram":
            # Instagram allows longer content, no specific limits
            pass
        elif platform == "facebook":
            # Facebook allows long content, no specific limits
            pass
        
        return response_text
    
    def _calculate_confidence_score(
        self,
        analysis: Dict[str, Any],
        knowledge_entries: List[CompanyKnowledge],
        template: Optional[ResponseTemplate]
    ) -> float:
        """Calculate confidence score for the generated response"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we have relevant knowledge
        if knowledge_entries:
            confidence += 0.2
        
        # Boost confidence if we used a template
        if template:
            confidence += 0.2
        
        # Adjust based on intent clarity
        intent = analysis.get('intent', 'general')
        if intent in ['question', 'complaint', 'lead']:
            confidence += 0.1  # Clear intents are easier to respond to
        
        return min(1.0, confidence)
    
    def _generate_fallback_response(
        self,
        interaction: SocialInteraction,
        analysis: Dict[str, Any],
        personality_style: str
    ) -> Dict[str, Any]:
        """Generate a safe fallback response when AI generation fails"""
        
        intent = analysis.get('intent', 'general')
        
        fallback_responses = {
            "question": "Thank you for your question! We'll get back to you with more details soon.",
            "complaint": "We apologize for any inconvenience. Please send us a direct message so we can resolve this for you.",
            "praise": "Thank you so much for your kind words! We really appreciate your support.",
            "lead": "Thank you for your interest! Please reach out to us directly and we'll be happy to help.",
            "general": "Thank you for reaching out! We appreciate your engagement with our content."
        }
        
        response_text = fallback_responses.get(intent, fallback_responses["general"])
        
        return {
            "response_text": response_text,
            "confidence_score": 0.3,
            "personality_style": personality_style,
            "template_used": None,
            "knowledge_sources": [],
            "response_reasoning": f"Fallback response for {intent} intent"
        }
    
    async def process_interaction(
        self,
        interaction_id: str,
        user_id: int,
        personality_style: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Main method to process an interaction and generate a response.
        
        Args:
            interaction_id: ID of the interaction to process
            user_id: User ID
            personality_style: Personality style to use
            
        Returns:
            Generated response data or None if processing fails
        """
        try:
            # Get the interaction
            interaction = self.db.query(SocialInteraction).filter(
                SocialInteraction.id == interaction_id,
                SocialInteraction.user_id == user_id
            ).first()
            
            if not interaction:
                logger.error(f"Interaction {interaction_id} not found")
                return None
            
            # Get user's default personality style if not provided
            if personality_style is None:
                user_settings = self.db.query(UserSetting).filter(
                    UserSetting.user_id == user_id
                ).first()
                personality_style = (
                    user_settings.default_response_personality 
                    if user_settings and user_settings.default_response_personality 
                    else "professional"
                )
            
            # Analyze the interaction
            analysis = self.analyze_interaction_intent(interaction.content)
            
            # Update interaction with analysis results
            interaction.sentiment = analysis.get('sentiment', 'neutral')
            interaction.intent = analysis.get('intent', 'general')
            interaction.priority_score = analysis.get('priority_score', 50)
            
            # Search for relevant company knowledge
            keywords = analysis.get('keywords', [])
            if interaction.content:
                # Extract additional keywords from content
                additional_keywords = re.findall(r'\b\w+\b', interaction.content.lower())
                keywords.extend(additional_keywords[:5])  # Add up to 5 content keywords
            
            knowledge_entries = self.search_company_knowledge(
                user_id, keywords, context_type="customer_service"
            )
            
            # Find matching template
            template = self.find_matching_template(
                user_id, analysis['intent'], interaction.platform, keywords
            )
            
            # Generate personalized response
            response_data = self.generate_personalized_response(
                interaction, analysis, knowledge_entries, template, personality_style
            )
            
            # Update usage counts
            for entry in knowledge_entries:
                entry.usage_count = (entry.usage_count or 0) + 1
                entry.last_used_at = datetime.now(timezone.utc)
            
            if template:
                template.usage_count = (template.usage_count or 0) + 1
            
            self.db.commit()
            
            logger.info(f"Generated response for interaction {interaction_id} with {response_data['confidence_score']:.2f} confidence")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to process interaction {interaction_id}: {e}")
            self.db.rollback()
            return None


# Global instance
def get_personality_engine(db: Session) -> PersonalityResponseEngine:
    """Get a PersonalityResponseEngine instance"""
    return PersonalityResponseEngine(db)