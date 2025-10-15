import { AlertTriangle, Sparkles, RotateCcw } from 'lucide-react';

interface DemoModeToggleProps {
  onGenerateSamples: () => void;
  onClearSamples: () => void;
  hasSamples: boolean;
  isGenerating: boolean;
}

export function DemoModeToggle({ 
  onGenerateSamples, 
  onClearSamples, 
  hasSamples,
  isGenerating 
}: DemoModeToggleProps) {
  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200 rounded-xl p-6 mb-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-bold text-gray-800">
              Portfolio Showcase Mode
            </h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            {hasSamples ? (
              <>
                <span className="font-semibold text-purple-700">🎬 Demo mode active:</span> Displaying sample anomalies to showcase AI analysis capabilities. 
                These are realistic scenarios based on LADWP's typical grid patterns.
              </>
            ) : (
              <>
                <span className="font-semibold text-gray-700">No real anomalies detected.</span> Generate fake sample anomalies to demonstrate the AI-powered recommendation system. 
                Perfect for showcasing capabilities during normal grid operations.
              </>
            )}
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <AlertTriangle className="w-4 h-4" />
            <span>
              {hasSamples 
                ? 'Sample scenarios generated for demonstration purposes'
                : 'Click below to generate realistic sample scenarios'
              }
            </span>
          </div>
        </div>

        <div className="flex gap-2">
          {hasSamples ? (
            <button
              onClick={onClearSamples}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-semibold text-sm transition-all flex items-center gap-2 shadow-lg"
            >
              <RotateCcw className="w-4 h-4" />
              Clear Samples
            </button>
          ) : (
            <button
              onClick={onGenerateSamples}
              disabled={isGenerating}
              className={`px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 shadow-lg ${
                isGenerating
                  ? 'bg-gray-400 cursor-wait text-white'
                  : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white transform hover:scale-105'
              }`}
            >
              <Sparkles className="w-5 h-5" />
              {isGenerating ? 'Generating...' : 'Generate Sample Scenarios'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
