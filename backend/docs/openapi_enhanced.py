"""
Enhanced OpenAPI Documentation Generator
Comprehensive documentation for all social media integration endpoints
"""
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def generate_enhanced_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate enhanced OpenAPI schema with comprehensive integration documentation
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Enhanced OpenAPI schema
    """
    # Get base OpenAPI schema
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add comprehensive integration endpoint documentation
    integration_docs = {
        "/api/integrations/instagram/post": {
            "post": {
                "tags": ["integrations"],
                "summary": "Create Instagram Post",
                "description": """
                Create a new Instagram post with media content.
                
                **Features:**
                - Support for images, videos, carousels, and reels
                - Automatic hashtag optimization
                - Location tagging support
                - Publishing rate limit compliance
                
                **Rate Limits:**
                - 25 posts per hour per Instagram Business Account
                - Content publishing API limits apply
                
                **Media Requirements:**
                - Images: JPG, PNG (max 8MB, aspect ratio 1:1, 4:5, or 1.91:1)
                - Videos: MP4, MOV (max 100MB, max 60s for feed, 90s for reels)
                - Carousels: 2-10 items maximum
                """,
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["caption", "media_urls", "media_type"],
                                "properties": {
                                    "caption": {
                                        "type": "string",
                                        "maxLength": 2200,
                                        "description": "Post caption with optional hashtags",
                                        "example": "Check out this amazing sunset! #photography #nature #beautiful"
                                    },
                                    "media_urls": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "uri"},
                                        "minItems": 1,
                                        "maxItems": 10,
                                        "description": "URLs of media files to post",
                                        "example": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
                                    },
                                    "media_type": {
                                        "type": "string",
                                        "enum": ["IMAGE", "VIDEO", "CAROUSEL_ALBUM", "REELS"],
                                        "description": "Type of Instagram media",
                                        "example": "CAROUSEL_ALBUM"
                                    },
                                    "location_id": {
                                        "type": "string",
                                        "description": "Instagram location ID for geo-tagging",
                                        "nullable": True,
                                        "example": "213385402"
                                    },
                                    "hashtags": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "maxItems": 30,
                                        "description": "Additional hashtags to include",
                                        "example": ["sunset", "photography", "nature"]
                                    },
                                    "schedule_for": {
                                        "type": "string",
                                        "format": "date-time",
                                        "description": "Schedule post for future publishing",
                                        "nullable": True
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Post created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "instagram_post_id": {"type": "string", "example": "18052716124312345"},
                                        "permalink": {"type": "string", "example": "https://www.instagram.com/p/ABC123/"},
                                        "content_id": {"type": "integer", "example": 12345}
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Instagram account not connected or invalid token",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {"type": "string", "example": "Instagram account not connected"}
                                    }
                                }
                            }
                        }
                    },
                    "429": {
                        "description": "Rate limit exceeded",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {"type": "string", "example": "Publishing rate limit exceeded. Try again in 1 hour."}
                                    }
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {"type": "string", "example": "Failed to create Instagram post: Media processing failed"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/integrations/facebook/post": {
            "post": {
                "tags": ["integrations"],
                "summary": "Create Facebook Post",
                "description": """
                Create a new Facebook post on connected Page.
                
                **Features:**
                - Text posts with optional media
                - Link sharing with automatic preview
                - Photo and video uploads
                - Scheduled publishing
                - Audience targeting
                
                **Rate Limits:**
                - 600 requests per 10 minutes per Page
                - Content posting limits may apply based on Page type
                
                **Media Support:**
                - Images: JPG, PNG, GIF (max 4MB)
                - Videos: MP4, MOV (max 1GB, max 240 minutes)
                """,
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["message"],
                                "properties": {
                                    "message": {
                                        "type": "string",
                                        "maxLength": 63206,
                                        "description": "Post message content",
                                        "example": "Exciting news! We're launching our new product line. Learn more at our website."
                                    },
                                    "media_urls": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "uri"},
                                        "description": "URLs of media files to attach",
                                        "example": ["https://example.com/product-image.jpg"]
                                    },
                                    "link": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "Link to include in post",
                                        "nullable": True,
                                        "example": "https://example.com/new-product"
                                    },
                                    "scheduled_publish_time": {
                                        "type": "string",
                                        "format": "date-time",
                                        "description": "Schedule post for future publishing",
                                        "nullable": True
                                    },
                                    "targeting": {
                                        "type": "object",
                                        "description": "Audience targeting options",
                                        "properties": {
                                            "countries": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Target countries (ISO codes)"
                                            },
                                            "age_min": {"type": "integer", "minimum": 13},
                                            "age_max": {"type": "integer", "maximum": 65}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Post created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "facebook_post_id": {"type": "string", "example": "123456789_987654321"},
                                        "content_id": {"type": "integer", "example": 12345}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/integrations/tiktok/video": {
            "post": {
                "tags": ["integrations"],
                "summary": "Upload TikTok Video",
                "description": """
                Upload a video to TikTok with comprehensive options.
                
                **Features:**
                - Video upload with description
                - Privacy controls (public, friends, private)
                - Interactive features (duet, stitch, comments)
                - Brand content settings
                - Auto music addition
                
                **Rate Limits:**
                - Very strict: 10 requests per day per developer app
                - Production apps may have higher limits
                
                **Video Requirements:**
                - Format: MP4, WebM, MOV
                - Resolution: 720x1280 minimum (9:16 aspect ratio recommended)
                - Duration: 15 seconds to 10 minutes
                - Size: Up to 4GB
                """,
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["video_url", "description"],
                                "properties": {
                                    "video_url": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "URL of video file to upload",
                                        "example": "https://example.com/video.mp4"
                                    },
                                    "description": {
                                        "type": "string",
                                        "maxLength": 2200,
                                        "description": "Video description with hashtags",
                                        "example": "Amazing dance moves! #dance #trending #fyp"
                                    },
                                    "privacy_level": {
                                        "type": "string",
                                        "enum": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR", "SELF_ONLY"],
                                        "default": "PUBLIC_TO_EVERYONE",
                                        "description": "Video privacy setting"
                                    },
                                    "disable_duet": {
                                        "type": "boolean",
                                        "default": False,
                                        "description": "Disable duet feature for this video"
                                    },
                                    "disable_stitch": {
                                        "type": "boolean",
                                        "default": False,
                                        "description": "Disable stitch feature for this video"
                                    },
                                    "disable_comment": {
                                        "type": "boolean",
                                        "default": False,
                                        "description": "Disable comments on this video"
                                    },
                                    "brand_content_toggle": {
                                        "type": "boolean",
                                        "default": False,
                                        "description": "Mark as branded content"
                                    },
                                    "auto_add_music": {
                                        "type": "boolean",
                                        "default": True,
                                        "description": "Auto-add music from TikTok library"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Video uploaded successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "publish_id": {"type": "string", "example": "v0f034gf0f30f03f0"},
                                        "content_id": {"type": "integer", "example": 12345},
                                        "platform": {"type": "string", "example": "tiktok"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/integrations/metrics/collection": {
            "get": {
                "tags": ["integrations"],
                "summary": "Get Metrics Collection Status",
                "description": """
                Get real-time metrics collection status across all connected platforms.
                
                **Features:**
                - Platform-specific collection status
                - Last collection timestamps
                - Collection intervals and schedules
                - Total metrics count
                - Error reporting
                
                **Collection Intervals:**
                - Twitter: Every 15 minutes
                - Instagram: Every hour
                - Facebook: Every hour
                - LinkedIn: Every 2 hours
                - TikTok: Every 2 hours
                """,
                "responses": {
                    "200": {
                        "description": "Metrics collection status retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "collection_status": {
                                            "type": "object",
                                            "properties": {
                                                "last_update": {"type": "string", "format": "date-time"},
                                                "platforms": {
                                                    "type": "object",
                                                    "properties": {
                                                        "twitter": {
                                                            "type": "object",
                                                            "properties": {
                                                                "status": {"type": "string", "example": "active"},
                                                                "last_collection": {"type": "string", "format": "date-time"},
                                                                "next_collection": {"type": "string", "format": "date-time"},
                                                                "metrics_count": {"type": "integer", "example": 150},
                                                                "error_count": {"type": "integer", "example": 0}
                                                            }
                                                        },
                                                        "instagram": {
                                                            "type": "object",
                                                            "properties": {
                                                                "status": {"type": "string", "example": "active"},
                                                                "last_collection": {"type": "string", "format": "date-time"},
                                                                "next_collection": {"type": "string", "format": "date-time"},
                                                                "metrics_count": {"type": "integer", "example": 89},
                                                                "error_count": {"type": "integer", "example": 1}
                                                            }
                                                        }
                                                    }
                                                },
                                                "total_metrics": {"type": "integer", "example": 1247}
                                            }
                                        },
                                        "last_collection": {"type": "string", "format": "date-time"},
                                        "platforms": {
                                            "type": "object",
                                            "description": "Platform-specific status details"
                                        },
                                        "metrics_count": {"type": "integer", "example": 1247}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add quota management documentation
    quota_docs = {
        "/api/quota/status": {
            "get": {
                "tags": ["integrations"],
                "summary": "Get API Quota Status",
                "description": """
                Get current API quota utilization across all platforms.
                
                **Features:**
                - Real-time quota monitoring
                - Platform-specific limits
                - Utilization percentages
                - Reset times and windows
                - Burst capacity status
                
                **Quota Limits:**
                - Twitter: 300 requests per 15 minutes
                - Instagram: 200 requests per hour
                - Facebook: 600 requests per 10 minutes
                - LinkedIn: 100 requests per hour
                - TikTok: 10 requests per day (very restrictive)
                """,
                "responses": {
                    "200": {
                        "description": "Quota status retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "quotas": {
                                            "type": "object",
                                            "additionalProperties": {
                                                "type": "object",
                                                "properties": {
                                                    "platform": {"type": "string"},
                                                    "current_usage": {"type": "integer"},
                                                    "quota_limit": {"type": "integer"},
                                                    "utilization_percent": {"type": "number", "format": "float"},
                                                    "status": {"type": "string", "enum": ["normal", "warning", "critical", "exceeded"]},
                                                    "reset_time": {"type": "string", "format": "date-time"},
                                                    "time_window": {"type": "integer", "description": "Window in seconds"},
                                                    "burst_available": {"type": "integer"}
                                                }
                                            }
                                        },
                                        "overall_status": {"type": "string", "enum": ["healthy", "degraded", "critical"]},
                                        "critical_platforms": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Merge enhanced documentation
    if "paths" not in openapi_schema:
        openapi_schema["paths"] = {}
    
    openapi_schema["paths"].update(integration_docs)
    openapi_schema["paths"].update(quota_docs)
    
    # Add comprehensive examples and schemas
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "examples" not in openapi_schema["components"]:
        openapi_schema["components"]["examples"] = {}
    
    # Add integration examples
    openapi_schema["components"]["examples"].update({
        "InstagramPostExample": {
            "summary": "Instagram Carousel Post",
            "description": "Example of creating a carousel post with multiple images",
            "value": {
                "caption": "Amazing sunset collection from our recent trip! 🌅 #photography #travel #sunset #nature",
                "media_urls": [
                    "https://example.com/sunset1.jpg",
                    "https://example.com/sunset2.jpg",
                    "https://example.com/sunset3.jpg"
                ],
                "media_type": "CAROUSEL_ALBUM",
                "hashtags": ["golden hour", "landscape", "vacation"]
            }
        },
        "FacebookPostExample": {
            "summary": "Facebook Business Post",
            "description": "Example of a business post with link and targeting",
            "value": {
                "message": "🚀 Exciting news! We're launching our new AI-powered social media management platform. Join thousands of businesses already using our solution to boost their social media presence.\n\nKey features:\n✅ AI content generation\n✅ Multi-platform posting\n✅ Advanced analytics\n✅ Automation workflows\n\nLearn more and start your free trial today!",
                "link": "https://aisocialagent.com/signup",
                "targeting": {
                    "countries": ["US", "CA", "GB"],
                    "age_min": 25,
                    "age_max": 55
                }
            }
        },
        "TikTokVideoExample": {
            "summary": "TikTok Dance Video",
            "description": "Example of uploading a dance video with all features enabled",
            "value": {
                "video_url": "https://example.com/dance-video.mp4",
                "description": "Learning this trending dance! Who wants to see the tutorial? 💃 #dance #trending #fyp #tutorial #viral",
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
                "brand_content_toggle": False,
                "auto_add_music": True
            }
        }
    })
    
    # Add security scheme information
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"].update({
        "Auth0Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Auth0 JWT token obtained from authentication flow"
        },
        "LocalJWT": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Local JWT token for development and testing"
        }
    })
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"Auth0Bearer": []},
        {"LocalJWT": []}
    ]
    
    # Add contact and external docs
    openapi_schema["externalDocs"] = {
        "description": "Complete API Documentation and Guides",
        "url": "https://docs.aisocialagent.com"
    }
    
    # Cache the schema
    app.openapi_schema = openapi_schema
    return openapi_schema

def add_integration_tags(app: FastAPI):
    """Add comprehensive tags for integration endpoints"""
    
    additional_tags = [
        {
            "name": "instagram",
            "description": "Instagram Business API integration for photos, videos, reels, and stories",
            "externalDocs": {
                "description": "Instagram Graph API Documentation",
                "url": "https://developers.facebook.com/docs/instagram-api/"
            }
        },
        {
            "name": "facebook", 
            "description": "Facebook Pages API integration for posts, insights, and page management",
            "externalDocs": {
                "description": "Facebook Graph API Documentation",
                "url": "https://developers.facebook.com/docs/graph-api/"
            }
        },
        {
            "name": "twitter",
            "description": "Twitter API v2 integration for tweets, threads, and analytics",
            "externalDocs": {
                "description": "Twitter API Documentation",
                "url": "https://developer.twitter.com/en/docs/twitter-api"
            }
        },
        {
            "name": "linkedin",
            "description": "LinkedIn API integration for professional content and company pages",
            "externalDocs": {
                "description": "LinkedIn API Documentation", 
                "url": "https://docs.microsoft.com/en-us/linkedin/"
            }
        },
        {
            "name": "tiktok",
            "description": "TikTok API integration for video uploads and analytics",
            "externalDocs": {
                "description": "TikTok for Developers",
                "url": "https://developers.tiktok.com/"
            }
        },
        {
            "name": "quota-management",
            "description": "API quota monitoring and rate limiting management"
        },
        {
            "name": "metrics-collection",
            "description": "Real-time metrics collection and performance tracking"
        }
    ]
    
    # Extend existing tags
    if hasattr(app, 'openapi_tags') and app.openapi_tags:
        app.openapi_tags.extend(additional_tags)
    else:
        app.openapi_tags = additional_tags

# Usage example for integration with main FastAPI app
def setup_enhanced_openapi(app: FastAPI):
    """
    Set up enhanced OpenAPI documentation for the application
    
    Args:
        app: FastAPI application instance
    """
    # Add integration tags
    add_integration_tags(app)
    
    # Override the openapi method to use enhanced schema
    def custom_openapi():
        return generate_enhanced_openapi_schema(app)
    
    app.openapi = custom_openapi
    
    return app