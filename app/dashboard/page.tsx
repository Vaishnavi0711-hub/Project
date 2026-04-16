'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import MessageAnalyzer from '@/components/MessageAnalyzer'
import AudioAnalyzer from '@/components/AudioAnalyzer'
import ResultsPanel from '@/components/ResultsPanel'

export default function Dashboard() {
  const [analysisResults, setAnalysisResults] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'text' | 'audio'>('text')

  const handleTextAnalysis = async (text: string) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/analyze-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const data = await response.json()
      setAnalysisResults(data)
    } catch (error) {
      console.error('Analysis error:', error)
      setAnalysisResults({
        error: 'Failed to analyze text. Please try again.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleAudioAnalysis = async (file: File) => {
    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch('/api/analyze-audio', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      setAnalysisResults(data)
    } catch (error) {
      console.error('Analysis error:', error)
      setAnalysisResults({
        error: 'Failed to analyze audio. Please try again.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border sticky top-0 bg-background/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-primary" />
            <span className="text-xl font-bold text-primary">TRUST.AI</span>
          </Link>
          <Button variant="outline" asChild>
            <Link href="/">Back Home</Link>
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-8">
          {/* Title */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold text-foreground">
              Analyze Suspicious Messages & Calls
            </h1>
            <p className="text-muted-foreground">
              Upload text or audio to check if it&apos;s a scam. Results are instant and private.
            </p>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 justify-center">
            <Button
              onClick={() => setActiveTab('text')}
              variant={activeTab === 'text' ? 'default' : 'outline'}
              className="px-6"
            >
              Text Messages
            </Button>
            <Button
              onClick={() => setActiveTab('audio')}
              variant={activeTab === 'audio' ? 'default' : 'outline'}
              className="px-6"
            >
              Audio Calls
            </Button>
          </div>

          {/* Main Content */}
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left: Input Panel */}
            <div className="space-y-4">
              {activeTab === 'text' && (
                <MessageAnalyzer
                  onAnalyze={handleTextAnalysis}
                  isLoading={isLoading}
                />
              )}
              {activeTab === 'audio' && (
                <AudioAnalyzer
                  onAnalyze={handleAudioAnalysis}
                  isLoading={isLoading}
                />
              )}
            </div>

            {/* Right: Results Panel */}
            <div className="space-y-4">
              {analysisResults && (
                <ResultsPanel
                  results={analysisResults}
                  type={activeTab}
                />
              )}
              {!analysisResults && !isLoading && (
                <div className="bg-card rounded-lg border border-border p-8 text-center h-full flex items-center justify-center">
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto flex items-center justify-center">
                      <Shield className="w-8 h-8 text-primary" />
                    </div>
                    <p className="text-muted-foreground">
                      {activeTab === 'text'
                        ? 'Paste a message above to analyze'
                        : 'Upload an audio file to analyze'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
