import { useState, useEffect } from 'react'

const ProgressBar = ({ 
  isActive = false, 
  stages = ['Initializing...', 'Processing...', 'Finalizing...'],
  duration = 5000,
  onComplete = () => {}
}) => {
  const [currentStage, setCurrentStage] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isActive) {
      setProgress(0)
      setCurrentStage(0)
      return
    }

    const stageInterval = duration / stages.length
    const updateInterval = 100 // Update every 100ms for smooth animation
    
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + (100 / (duration / updateInterval))
        
        // Update stage based on progress
        const newStage = Math.floor((newProgress / 100) * stages.length)
        if (newStage !== currentStage && newStage < stages.length) {
          setCurrentStage(newStage)
        }
        
        if (newProgress >= 100) {
          clearInterval(interval)
          onComplete()
          return 100
        }
        
        return newProgress
      })
    }, updateInterval)

    return () => clearInterval(interval)
  }, [isActive, duration, stages, currentStage, onComplete])

  if (!isActive) return null

  return (
    <div className="w-full space-y-3">
      {/* Progress Bar */}
      <div className="relative">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>{stages[currentStage] || stages[stages.length - 1]}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-200 ease-out relative overflow-hidden"
            style={{ width: `${progress}%` }}
          >
            {/* Animated shimmer effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-60 animate-pulse"></div>
          </div>
        </div>
      </div>
      
      {/* Stage indicators */}
      <div className="flex justify-between">
        {stages.map((stage, index) => (
          <div 
            key={index}
            className={`flex flex-col items-center space-y-1 text-xs ${
              index <= currentStage ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <div className={`w-3 h-3 rounded-full border-2 ${
              index <= currentStage 
                ? 'bg-blue-600 border-blue-600' 
                : 'bg-gray-200 border-gray-300'
            } ${index === currentStage ? 'animate-pulse' : ''}`}></div>
            <span className="text-center max-w-20 leading-tight">
              {stage.replace('...', '')}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ProgressBar