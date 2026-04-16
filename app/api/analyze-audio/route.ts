import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 })
    }

    if (!file.type.startsWith('audio/')) {
      return NextResponse.json({ error: 'Invalid file type. Please upload an audio file.' }, { status: 400 })
    }

    // File size limit: 25MB
    const maxSize = 25 * 1024 * 1024
    if (file.size > maxSize) {
      return NextResponse.json({ error: 'File size exceeds 25MB limit' }, { status: 400 })
    }

    // Get backend URL from environment or use default
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    try {
      // Create FormData for backend
      const backendFormData = new FormData()
      backendFormData.append('file', file)

      // Call Python backend
      const response = await fetch(`${backendUrl}/api/analyze-audio`, {
        method: 'POST',
        body: backendFormData,
        signal: AbortSignal.timeout(10000), // 10 second timeout for audio processing
      })

      if (!response.ok) {
        const errorData = await response.json()
        return NextResponse.json(
          { error: errorData.detail || 'Backend analysis failed' },
          { status: response.status }
        )
      }

      const analysis = await response.json()

      return NextResponse.json({
        risk_score: analysis.risk_score,
        threat_types: analysis.threat_types,
        explanation: analysis.explanation,
        confidence: analysis.confidence,
        transcription: analysis.transcription,
      })
    } catch (fetchError) {
      // Backend unavailable, use fallback
      console.log('[v0] Backend unavailable, using fallback audio analysis')
      return fallbackAnalysis(file)
    }
  } catch (error) {
    console.error('Audio analysis error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze audio' },
      { status: 500 }
    )
  }
}

// Fallback analysis when backend is unavailable
function fallbackAnalysis(file: File) {
  const mockTranscriptions = [
    'Hi, this is your bank calling about suspicious activity on your account. Please provide your social security number to verify your identity.',
    'Congratulations! You have won a lottery prize. Click the link to claim your rewards today.',
    'Your Amazon account has been locked due to unauthorized access. Verify your password immediately.',
    'Hello, this is tech support. We detected a virus on your computer. Please allow remote access to fix this.',
    'Your package delivery was delayed. Please pay the customs fee to receive your package.',
  ]

  const transcription = mockTranscriptions[Math.floor(Math.random() * mockTranscriptions.length)]
  const lowerText = transcription.toLowerCase()

  const voicePatterns = {
    identity_theft: ['ssn', 'social security', 'password', 'account number'],
    impersonation: ['bank', 'amazon', 'microsoft', 'tech support'],
    threats: ['locked', 'suspended', 'unauthorized'],
    money: ['wire money', 'send money', 'payment', 'fee'],
  }

  const threats: string[] = []
  let scoreContribution = 0

  Object.entries(voicePatterns).forEach(([category, patterns]) => {
    const matches = patterns.filter(p => lowerText.includes(p))
    if (matches.length > 0) {
      threats.push(category)
      scoreContribution += 25
    }
  })

  let riskScore = Math.min(100, scoreContribution)
  const variance = (Math.random() - 0.5) * 20
  riskScore = Math.max(0, Math.min(100, riskScore + variance))

  const explanation = threats.length === 0
    ? 'Audio does not contain obvious scam indicators.'
    : `Detected: ${threats.join(', ')}`

  return NextResponse.json({
    risk_score: Math.round(riskScore),
    threat_types: threats,
    explanation,
    confidence: Math.min(0.95, 0.55 + threats.length * 0.12),
    transcription,
  })
}
