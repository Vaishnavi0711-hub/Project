'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Zap } from 'lucide-react'

interface MessageAnalyzerProps {
  onAnalyze: (text: string) => void
  isLoading: boolean
}

export default function MessageAnalyzer({ onAnalyze, isLoading }: MessageAnalyzerProps) {
  const [message, setMessage] = useState('')

  const handleAnalyze = () => {
    if (message.trim()) {
      onAnalyze(message)
    }
  }

  const handlePasteExample = (example: string) => {
    setMessage(example)
  }

  return (
    <Card className="p-6 space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-semibold text-foreground">
          Paste or type a message
        </label>
        <Textarea
          placeholder="Paste a suspicious message here... Example: 'Urgent! Your account has been compromised. Click here to verify your identity.'"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="min-h-40 resize-none"
          disabled={isLoading}
        />
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground">Example scam messages:</p>
        <div className="flex flex-col gap-2">
          <button
            onClick={() =>
              handlePasteExample(
                'Click here immediately! Your PayPal account will be limited. Verify your account now: http://paypal-verify.com'
              )
            }
            disabled={isLoading}
            className="text-left text-xs p-2 rounded border border-border hover:bg-muted transition disabled:opacity-50"
          >
            Phishing example
          </button>
          <button
            onClick={() =>
              handlePasteExample('You have won $1,000,000! Claim your prize now by sending $50 for processing fees.')
            }
            disabled={isLoading}
            className="text-left text-xs p-2 rounded border border-border hover:bg-muted transition disabled:opacity-50"
          >
            Prize scam example
          </button>
          <button
            onClick={() =>
              handlePasteExample('Hi, your bank detected suspicious activity. Verify your credentials: bankverify.net')
            }
            disabled={isLoading}
            className="text-left text-xs p-2 rounded border border-border hover:bg-muted transition disabled:opacity-50"
          >
            Bank fraud example
          </button>
        </div>
      </div>

      <Button
        onClick={handleAnalyze}
        disabled={!message.trim() || isLoading}
        className="w-full bg-primary hover:bg-primary/90"
      >
        {isLoading ? (
          <>
            <Spinner className="w-4 h-4 mr-2" />
            Analyzing...
          </>
        ) : (
          <>
            <Zap className="w-4 h-4 mr-2" />
            Analyze Message
          </>
        )}
      </Button>

      <p className="text-xs text-muted-foreground text-center">
        Your message is analyzed locally. Nothing is stored or shared.
      </p>
    </Card>
  )
}
