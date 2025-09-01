import React from 'react'
import { Link } from 'react-router-dom'
import { 
  ChartBarIcon, 
  ClockIcon, 
  SparklesIcon, 
  UserGroupIcon,
  LightBulbIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

const LandingPage = () => {
  const features = [
    {
      icon: SparklesIcon,
      title: "AI-Powered Content Creation",
      description: "Generate engaging social media content with advanced AI that understands your brand voice and audience."
    },
    {
      icon: ClockIcon,
      title: "Smart Scheduling",
      description: "Automatically schedule posts at optimal times across all your social media platforms for maximum engagement."
    },
    {
      icon: ChartBarIcon,
      title: "Advanced Analytics",
      description: "Track performance, analyze engagement patterns, and get actionable insights to grow your social presence."
    },
    {
      icon: UserGroupIcon,
      title: "Multi-Platform Management",
      description: "Manage Twitter, LinkedIn, Instagram, and Facebook from one unified dashboard."
    },
    {
      icon: LightBulbIcon,
      title: "Content Memory System",
      description: "AI remembers your past content and audience preferences to create more relevant and engaging posts."
    },
    {
      icon: ShieldCheckIcon,
      title: "Enterprise Security",
      description: "Bank-level security with encrypted storage and multi-tenant architecture for team collaboration."
    }
  ]

  const testimonials = [
    {
      quote: "Lily AI transformed our social media strategy. We've seen a 300% increase in engagement since switching.",
      author: "Sarah Chen",
      role: "Marketing Director",
      company: "TechFlow Inc."
    },
    {
      quote: "The AI content generation is incredibly accurate to our brand voice. It's like having a full marketing team.",
      author: "Marcus Rodriguez",
      role: "Founder",
      company: "GrowthLabs"
    },
    {
      quote: "Finally, a social media tool that actually understands context and creates meaningful content.",
      author: "Emily Watson",
      role: "Content Manager",
      company: "InnovateNow"
    }
  ]

  const pricingTiers = [
    {
      name: "Starter",
      price: "$199",
      period: "per month",
      description: "Perfect for small businesses and solopreneurs",
      features: [
        "3 social media accounts",
        "AI content generation",
        "Basic scheduling",
        "Performance analytics",
        "Email support"
      ],
      cta: "Start Free Trial",
      popular: false
    },
    {
      name: "Professional",
      price: "$499",
      period: "per month",
      description: "For growing businesses and marketing teams",
      features: [
        "10 social media accounts",
        "Advanced AI content creation",
        "Smart scheduling optimization",
        "Advanced analytics & insights",
        "Team collaboration",
        "Autonomous AI comment & messaging replies",
        "Priority support"
      ],
      cta: "Start Free Trial",
      popular: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "pricing",
      description: "For large organizations with custom needs",
      features: [
        "Unlimited social accounts",
        "Custom AI training",
        "Advanced security & compliance",
        "Dedicated account manager",
        "Custom integrations",
        "24/7 phone support"
      ],
      cta: "Contact Sales",
      popular: false
    }
  ]

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-indigo-600">Lily AI</h1>
              </div>
              <div className="hidden md:block ml-10">
                <div className="flex items-baseline space-x-8">
                  <a href="#features" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">Features</a>
                  <a href="#testimonials" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">Testimonials</a>
                  <a href="#pricing" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">Pricing</a>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-16 sm:pt-24 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
              AI-Powered Social Media
              <span className="text-indigo-600 block">Made Simple</span>
            </h1>
            <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
              Transform your social media presence with intelligent content creation, 
              automated scheduling, and powerful analytics. Let AI handle the heavy lifting 
              while you focus on growing your business.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/register"
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors inline-flex items-center justify-center"
              >
                Start Free Trial
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
              <Link
                to="/login"
                className="border-2 border-gray-300 hover:border-gray-400 text-gray-700 px-8 py-4 rounded-lg text-lg font-semibold transition-colors"
              >
                Sign In
              </Link>
            </div>
            <p className="mt-4 text-sm text-gray-500">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Everything you need to dominate social media
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Powerful features designed to scale your social media presence
            </p>
          </div>
          <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white rounded-xl p-8 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-lg">
                  <feature.icon className="h-6 w-6 text-indigo-600" />
                </div>
                <h3 className="mt-6 text-xl font-semibold text-gray-900">{feature.title}</h3>
                <p className="mt-4 text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Trusted by thousands of businesses
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              See what our customers are saying about Lily AI
            </p>
          </div>
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white rounded-xl p-8 shadow-sm">
                <p className="text-gray-600 text-lg italic">"{testimonial.quote}"</p>
                <div className="mt-6">
                  <div className="font-semibold text-gray-900">{testimonial.author}</div>
                  <div className="text-gray-600">{testimonial.role}</div>
                  <div className="text-indigo-600 font-medium">{testimonial.company}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Choose the plan that's right for your business
            </p>
          </div>
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingTiers.map((tier, index) => (
              <div
                key={index}
                className={`bg-white rounded-xl p-8 shadow-sm relative ${
                  tier.popular ? 'ring-2 ring-indigo-600 transform scale-105' : ''
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-indigo-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-gray-900">{tier.name}</h3>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-gray-900">{tier.price}</span>
                    <span className="text-gray-600">/{tier.period}</span>
                  </div>
                  <p className="mt-4 text-gray-600">{tier.description}</p>
                </div>
                <ul className="mt-8 space-y-4">
                  {tier.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center">
                      <CheckCircleIcon className="h-5 w-5 text-indigo-600 flex-shrink-0" />
                      <span className="ml-3 text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8">
                  <Link
                    to="/register"
                    className={`w-full px-6 py-3 rounded-lg font-semibold text-center block transition-colors ${
                      tier.popular
                        ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                    }`}
                  >
                    {tier.cta}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
            Ready to transform your social media presence?
          </h2>
          <p className="mt-4 text-xl text-gray-600">
            Join thousands of businesses already growing with Lily AI
          </p>
          <div className="mt-10">
            <Link
              to="/register"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors inline-flex items-center"
            >
              Start Your Free Trial Today
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            14-day free trial • No setup fees • Cancel anytime
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <h3 className="text-2xl font-bold text-white">Lily AI</h3>
              <p className="mt-4 text-gray-300 max-w-md">
                The most intelligent social media management platform. 
                Create, schedule, and optimize your content with AI.
              </p>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-white">Product</h4>
              <ul className="mt-4 space-y-2">
                <li><a href="#features" className="text-gray-300 hover:text-white">Features</a></li>
                <li><a href="#pricing" className="text-gray-300 hover:text-white">Pricing</a></li>
                <li><Link to="/login" className="text-gray-300 hover:text-white">Sign In</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-white">Company</h4>
              <ul className="mt-4 space-y-2">
                <li><a href="#" className="text-gray-300 hover:text-white">About</a></li>
                <li><a href="#" className="text-gray-300 hover:text-white">Privacy</a></li>
                <li><a href="#" className="text-gray-300 hover:text-white">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-gray-700 text-center">
            <p className="text-gray-400">
              © 2025 Lily AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage