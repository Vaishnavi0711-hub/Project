'use client'

import { Card } from '@/components/ui/card'
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react'

interface ResultsPanelProps {
  results: {
    risk_score?: number
    threat_types?: string[]
    explanation?: string
    confidence?: number
    error?: string
    transcription?: string
  }
  type: 'text' | 'audio'
}

export default function ResultsPanel({ results, type }: ResultsPanelProps) {
  if (results.error) {
    return (
      <Card className="p-6 space-y-4 border-destructive/20 bg-destructive/5">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="font-semibold text-destructive">Error</h3>
            <p className="text-sm text-muted-foreground">{results.error}</p>
          </div>
        </div>
      </Card>
    )
  }

  const riskScore = results.risk_score ?? 0
  const isLow = riskScore < 30
  const isMedium = riskScore >= 30 && riskScore < 70
  const isHigh = riskScore >= 70

  const getRiskColor = () => {
    if (isLow) return 'text-green-600 dark:text-green-400'
    if (isMedium) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getRiskBgColor = () => {
    if (isLow) return 'bg-green-100 dark:bg-green-950'
    if (isMedium) return 'bg-yellow-100 dark:bg-yellow-950'
    return 'bg-red-100 dark:bg-red-950'
  }

  const getRiskLabel = () => {
    if (isLow) return 'Low Risk - Likely Safe'
    if (isMedium) return 'Medium Risk - Review Carefully'
    return 'High Risk - Likely a Scam'
  }

  const getRiskIcon = () => {
    if (isLow) return <CheckCircle2 className="w-6 h-6" />
    if (isMedium) return <AlertTriangle className="w-6 h-6" />
    return <AlertCircle className="w-6 h-6" />
  }

  return (
    <div className="space-y-4">
      {/* Risk Meter */}
      <Card className={`p-8 ${getRiskBgColor()}`}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={getRiskColor()}>{getRiskIcon()}</div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">Risk Assessment</p>
                <p className={`text-lg font-bold ${getRiskColor()}`}>{getRiskLabel()}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-4xl font-bold text-foreground">{riskScore}%</p>
              <p className="text-xs text-muted-foreground">Risk Score</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-muted/30 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all ${
                isLow ? 'bg-green-500' : isMedium ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${riskScore}%` }}
            ></div>
          </div>

          {/* Confidence */}
          {results.confidence && (
            <div className="flex justify-between items-center pt-2 border-t border-border/20">
              <p className="text-xs text-muted-foreground">Analysis Confidence</p>
              <p className="text-sm font-semibold">{(results.confidence * 100).toFixed(0)}%</p>
            </div>
          )}
        </div>
      </Card>

      {/* Transcription (for audio) */}
      {type === 'audio' && results.transcription && (
        <Card className="p-6 space-y-2">
          <p className="text-sm font-semibold">Transcription</p>
          <p className="text-sm text-muted-foreground leading-relaxed">{results.transcription}</p>
        </Card>
      )}

      {/* Threat Types */}
      {results.threat_types && results.threat_types.length > 0 && (
        <Card className="p-6 space-y-3">
          <p className="text-sm font-semibold">Detected Threats</p>
          <div className="space-y-2">
            {results.threat_types.map((threat: string, idx: number) => (
              <div
                key={idx}
                className="flex items-center gap-2 text-sm p-2 bg-muted/50 rounded"
              >
                <div className="w-2 h-2 bg-accent rounded-full flex-shrink-0" />
                <span className="capitalize">{threat.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Explanation */}
      {results.explanation && (
        <Card className="p-6 space-y-2">
          <p className="text-sm font-semibold">Why This Score?</p>
          <p className="text-sm text-muted-foreground leading-relaxed">{results.explanation}</p>
        </Card>
      )}

      {/* Safety Tips */}
      <Card className="p-6 space-y-3 border-primary/20 bg-primary/5">
        <p className="text-sm font-semibold flex items-center gap-2">
          <span className="text-lg">💡</span> Safety Tips
        </p>
        <ul className="text-xs text-muted-foreground space-y-1 ml-6 list-disc">
          <li>Never click links or download attachments from untrusted sources</li>
          <li>Banks never ask for passwords or account details via message or call</li>
          <li>Legitimate companies won&apos;t pressure you to act immediately</li>
          <li>Report suspicious messages to your service provider</li>
        </ul>
      </Card>
    </div>
  )
}
