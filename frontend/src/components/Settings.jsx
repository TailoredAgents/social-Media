import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Formik, Form, Field, ErrorMessage } from 'formik'
import * as Yup from 'yup'

// Validation schemas
const profileSchema = Yup.object().shape({
  companyName: Yup.string().required('Company name is required'),
  industry: Yup.string().required('Industry is required'),
  website: Yup.url('Please enter a valid URL'),
  description: Yup.string().max(500, 'Description must be less than 500 characters')
})

const socialSchema = Yup.object().shape({
  linkedinToken: Yup.string(),
  twitterToken: Yup.string(),
  instagramToken: Yup.string(),
  facebookToken: Yup.string()
})

const goalSchema = Yup.object().shape({
  goalType: Yup.string().required('Goal type is required'),
  targetValue: Yup.number().positive('Target value must be positive').required('Target value is required'),
  timeframe: Yup.string().required('Timeframe is required')
})

// Settings Section Component
const SettingsSection = ({ title, children, darkMode, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay }}
    className={`p-6 rounded-xl backdrop-blur-md ${
      darkMode ? 'bg-gray-800/80' : 'bg-white/80'
    } border border-gray-200/20 shadow-lg`}
  >
    <h3 className={`text-lg font-semibold mb-4 ${
      darkMode ? 'text-white' : 'text-gray-900'
    }`}>
      {title}
    </h3>
    {children}
  </motion.div>
)

// Toggle Switch Component
const ToggleSwitch = ({ label, description, enabled, onChange, darkMode }) => (
  <div className="flex items-center justify-between py-3">
    <div>
      <p className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        {label}
      </p>
      {description && (
        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          {description}
        </p>
      )}
    </div>
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        enabled ? 'bg-teal-500' : darkMode ? 'bg-gray-600' : 'bg-gray-200'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  </div>
)

// Plan Comparison Component
const PlanComparison = ({ darkMode }) => {
  const plans = [
    {
      name: 'Base',
      price: '$49',
      features: ['5 Social Accounts', 'Basic Analytics', 'Content Calendar', 'Email Support'],
      current: false
    },
    {
      name: 'Professional',
      price: '$99',
      features: ['15 Social Accounts', 'Advanced Analytics', 'AI Content Generation', 'Priority Support', 'Team Collaboration'],
      current: true
    },
    {
      name: 'Enterprise',
      price: '$199',
      features: ['Unlimited Accounts', 'Custom AI Training', 'White-label Solution', 'Dedicated Manager', 'API Access'],
      current: false
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {plans.map((plan, index) => (
        <motion.div
          key={plan.name}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: index * 0.1 }}
          className={`p-4 rounded-lg border-2 ${
            plan.current
              ? 'border-teal-500 bg-teal-50/10'
              : darkMode
              ? 'border-gray-700 bg-gray-700/50'
              : 'border-gray-200 bg-gray-50/50'
          } relative`}
        >
          {plan.current && (
            <div className="absolute -top-2 -right-2 bg-teal-500 text-white text-xs px-2 py-1 rounded-full">
              Current Plan
            </div>
          )}
          
          <div className="text-center mb-4">
            <h4 className={`text-lg font-semibold ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              {plan.name}
            </h4>
            <p className={`text-2xl font-bold ${
              plan.current ? 'text-teal-500' : darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              {plan.price}<span className="text-sm font-normal">/month</span>
            </p>
          </div>

          <ul className="space-y-2 mb-4">
            {plan.features.map((feature, idx) => (
              <li key={idx} className={`text-sm flex items-center ${
                darkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                <span className="text-teal-500 mr-2">✓</span>
                {feature}
              </li>
            ))}
          </ul>

          <button
            className={`w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              plan.current
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-teal-500 text-white hover:bg-teal-600'
            }`}
            disabled={plan.current}
          >
            {plan.current ? 'Current Plan' : 'Upgrade'}
          </button>
        </motion.div>
      ))}
    </div>
  )
}

// Main Settings Component
const Settings = ({ darkMode, searchQuery }) => {
  const [activeTab, setActiveTab] = useState('profile')
  const [settings, setSettings] = useState({
    autoPosting: true,
    aiContentGeneration: true,
    smartScheduling: true,
    analyticsReports: true,
    emailNotifications: true,
    pushNotifications: false,
    darkMode: darkMode,
    language: 'en',
    timezone: 'UTC-8'
  })

  const tabs = [
    { id: 'profile', name: 'Company Profile', icon: '🏢' },
    { id: 'social', name: 'Social Integrations', icon: '🔗' },
    { id: 'goals', name: 'Goals & Targets', icon: '🎯' },
    { id: 'features', name: 'Features', icon: '⚙️' },
    { id: 'notifications', name: 'Notifications', icon: '🔔' },
    { id: 'plan', name: 'Plan & Billing', icon: '💳' }
  ]

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className={`text-3xl font-bold ${
          darkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Settings & Customization
        </h1>
        <p className={`text-lg ${
          darkMode ? 'text-gray-400' : 'text-gray-600'
        }`}>
          Configure your AI social media agent to match your needs
        </p>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className={`rounded-xl backdrop-blur-md ${
          darkMode ? 'bg-gray-800/80' : 'bg-white/80'
        } border border-gray-200/20 shadow-lg p-2`}
      >
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-teal-500 text-white shadow-lg'
                  : darkMode
                  ? 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Company Profile */}
        {activeTab === 'profile' && (
          <SettingsSection title="Company Profile" darkMode={darkMode} delay={0.2}>
            <Formik
              initialValues={{
                companyName: 'Tailored Agents',
                industry: 'AI & Technology',
                website: 'https://tailoredagents.com',
                description: 'Custom AI solutions for businesses'
              }}
              validationSchema={profileSchema}
              onSubmit={(values) => {
                console.log('Profile updated:', values)
              }}
            >
              <Form className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      darkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Company Name
                    </label>
                    <Field
                      name="companyName"
                      className={`w-full p-3 rounded-lg border ${
                        darkMode 
                          ? 'bg-gray-700 border-gray-600 text-white' 
                          : 'bg-white border-gray-300 text-gray-900'
                      } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                    />
                    <ErrorMessage name="companyName" component="div" className="text-red-500 text-sm mt-1" />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      darkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Industry
                    </label>
                    <Field
                      as="select"
                      name="industry"
                      className={`w-full p-3 rounded-lg border ${
                        darkMode 
                          ? 'bg-gray-700 border-gray-600 text-white' 
                          : 'bg-white border-gray-300 text-gray-900'
                      } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                    >
                      <option value="">Select Industry</option>
                      <option value="AI & Technology">AI & Technology</option>
                      <option value="Marketing & Advertising">Marketing & Advertising</option>
                      <option value="E-commerce">E-commerce</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Finance">Finance</option>
                      <option value="Education">Education</option>
                    </Field>
                    <ErrorMessage name="industry" component="div" className="text-red-500 text-sm mt-1" />
                  </div>
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${
                    darkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    Website
                  </label>
                  <Field
                    name="website"
                    type="url"
                    className={`w-full p-3 rounded-lg border ${
                      darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                  />
                  <ErrorMessage name="website" component="div" className="text-red-500 text-sm mt-1" />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${
                    darkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    Company Description
                  </label>
                  <Field
                    as="textarea"
                    name="description"
                    rows={3}
                    className={`w-full p-3 rounded-lg border ${
                      darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                  />
                  <ErrorMessage name="description" component="div" className="text-red-500 text-sm mt-1" />
                </div>

                <button
                  type="submit"
                  className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
                >
                  Save Profile
                </button>
              </Form>
            </Formik>
          </SettingsSection>
        )}

        {/* Social Integrations */}
        {activeTab === 'social' && (
          <SettingsSection title="Social Media Integrations" darkMode={darkMode} delay={0.2}>
            <div className="space-y-6">
              {[
                { name: 'LinkedIn', icon: '💼', connected: true, color: 'blue' },
                { name: 'Twitter', icon: '🐦', connected: true, color: 'sky' },
                { name: 'Instagram', icon: '📸', connected: false, color: 'pink' },
                { name: 'Facebook', icon: '👥', connected: true, color: 'indigo' }
              ].map((platform) => (
                <div key={platform.name} className="flex items-center justify-between p-4 rounded-lg border border-gray-200/20">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{platform.icon}</span>
                    <div>
                      <p className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {platform.name}
                      </p>
                      <p className={`text-sm ${
                        platform.connected ? 'text-green-500' : darkMode ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        {platform.connected ? 'Connected' : 'Not connected'}
                      </p>
                    </div>
                  </div>
                  <button
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      platform.connected
                        ? 'bg-red-500 text-white hover:bg-red-600'
                        : 'bg-teal-500 text-white hover:bg-teal-600'
                    }`}
                  >
                    {platform.connected ? 'Disconnect' : 'Connect'}
                  </button>
                </div>
              ))}
            </div>
          </SettingsSection>
        )}

        {/* Goals & Targets */}
        {activeTab === 'goals' && (
          <SettingsSection title="Goals & Targets" darkMode={darkMode} delay={0.2}>
            <Formik
              initialValues={{
                goalType: 'followers',
                targetValue: 5000,
                timeframe: '3months'
              }}
              validationSchema={goalSchema}
              onSubmit={(values) => {
                console.log('Goal created:', values)
              }}
            >
              <Form className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      darkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Goal Type
                    </label>
                    <Field
                      as="select"
                      name="goalType"
                      className={`w-full p-3 rounded-lg border ${
                        darkMode 
                          ? 'bg-gray-700 border-gray-600 text-white' 
                          : 'bg-white border-gray-300 text-gray-900'
                      } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                    >
                      <option value="followers">Followers Growth</option>
                      <option value="engagement">Engagement Rate</option>
                      <option value="reach">Monthly Reach</option>
                      <option value="conversions">Conversions</option>
                    </Field>
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      darkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Target Value
                    </label>
                    <Field
                      name="targetValue"
                      type="number"
                      className={`w-full p-3 rounded-lg border ${
                        darkMode 
                          ? 'bg-gray-700 border-gray-600 text-white' 
                          : 'bg-white border-gray-300 text-gray-900'
                      } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      darkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Timeframe
                    </label>
                    <Field
                      as="select"
                      name="timeframe"
                      className={`w-full p-3 rounded-lg border ${
                        darkMode 
                          ? 'bg-gray-700 border-gray-600 text-white' 
                          : 'bg-white border-gray-300 text-gray-900'
                      } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                    >
                      <option value="1month">1 Month</option>
                      <option value="3months">3 Months</option>
                      <option value="6months">6 Months</option>
                      <option value="1year">1 Year</option>
                    </Field>
                  </div>
                </div>

                <button
                  type="submit"
                  className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
                >
                  Create Goal
                </button>
              </Form>
            </Formik>

            {/* Current Goals */}
            <div className="mt-6 space-y-3">
              <h4 className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Current Goals
              </h4>
              {[
                { type: 'Followers Growth', target: 5000, current: 2750, timeframe: '3 months' },
                { type: 'Engagement Rate', target: 5.0, current: 4.2, timeframe: '6 months' }
              ].map((goal, index) => (
                <div key={index} className="p-3 rounded-lg border border-gray-200/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {goal.type}
                    </span>
                    <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {goal.timeframe}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className="bg-teal-500 h-2 rounded-full"
                      style={{ width: `${(goal.current / goal.target) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                      {goal.current} / {goal.target}
                    </span>
                    <span className="text-teal-500">
                      {Math.round((goal.current / goal.target) * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </SettingsSection>
        )}

        {/* Features */}
        {activeTab === 'features' && (
          <SettingsSection title="AI Features & Automation" darkMode={darkMode} delay={0.2}>
            <div className="space-y-4">
              <ToggleSwitch
                label="Auto-Posting"
                description="Automatically publish approved content at optimal times"
                enabled={settings.autoPosting}
                onChange={(value) => updateSetting('autoPosting', value)}
                darkMode={darkMode}
              />
              <ToggleSwitch
                label="AI Content Generation"
                description="Generate content ideas and drafts using AI"
                enabled={settings.aiContentGeneration}
                onChange={(value) => updateSetting('aiContentGeneration', value)}
                darkMode={darkMode}
              />
              <ToggleSwitch
                label="Smart Scheduling"
                description="AI-powered optimal posting time recommendations"
                enabled={settings.smartScheduling}
                onChange={(value) => updateSetting('smartScheduling', value)}
                darkMode={darkMode}
              />
              <ToggleSwitch
                label="Analytics Reports"
                description="Automated weekly performance reports"
                enabled={settings.analyticsReports}
                onChange={(value) => updateSetting('analyticsReports', value)}
                darkMode={darkMode}
              />
            </div>
          </SettingsSection>
        )}

        {/* Notifications */}
        {activeTab === 'notifications' && (
          <SettingsSection title="Notification Preferences" darkMode={darkMode} delay={0.2}>
            <div className="space-y-4">
              <ToggleSwitch
                label="Email Notifications"
                description="Receive updates and reports via email"
                enabled={settings.emailNotifications}
                onChange={(value) => updateSetting('emailNotifications', value)}
                darkMode={darkMode}
              />
              <ToggleSwitch
                label="Push Notifications"
                description="Browser notifications for important events"
                enabled={settings.pushNotifications}
                onChange={(value) => updateSetting('pushNotifications', value)}
                darkMode={darkMode}
              />
            </div>

            <div className="mt-6 space-y-4">
              <h4 className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Notification Types
              </h4>
              {[
                'Content published successfully',
                'High engagement alert',
                'Goal milestone reached',
                'Weekly performance report',
                'Content approval needed'
              ].map((type, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-4 h-4 text-teal-600 bg-gray-100 border-gray-300 rounded focus:ring-teal-500"
                  />
                  <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    {type}
                  </span>
                </div>
              ))}
            </div>
          </SettingsSection>
        )}

        {/* Plan & Billing */}
        {activeTab === 'plan' && (
          <SettingsSection title="Plan & Billing" darkMode={darkMode} delay={0.2}>
            <PlanComparison darkMode={darkMode} />
          </SettingsSection>
        )}
      </div>
    </div>
  )
}

export default Settings