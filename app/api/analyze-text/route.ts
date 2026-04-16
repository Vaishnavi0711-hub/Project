import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { text } = await request.json()

    if (!text || typeof text !== 'string' || text.trim().length === 0) {
      return NextResponse.json({ error: 'Invalid text provided' }, { status: 400 })
    }

    // Get backend URL from environment or use default
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    try {
      // Call Python backend
      const response = await fetch(`${backendUrl}/api/analyze-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
        signal: AbortSignal.timeout(5000), // 5 second timeout
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
      })
    } catch (fetchError) {
      // Backend unavailable, use fallback
      console.log('[v0] Backend unavailable, using fallback analysis')
      return fallbackAnalysis(text)
    }
  } catch (error) {
    console.error('Text analysis error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze text' },
      { status: 500 }
    )
  }
}

// Fallback analysis when backend is unavailable
function fallbackAnalysis(text: string) {
  const scamKeywords = {
    urgency: ['urgent', 'immediately', 'now', 'asap', 'verify now', 'act now', 'confirm now'],
    financial: ['wire money', 'send money', 'bitcoin', 'payment', 'transfer', 'cash', 'credit card'],
    identity: ['verify', 'confirm', 'identity', 'password', 'pin', 'credentials', 'ssn'],
    threat: ['limited', 'suspended', 'locked', 'frozen', 'compromised', 'unauthorized'],
    phishing: ['click here', 'click link', 'http://', 'verify account', 'update payment', 'reactivate'],
  }

  const lowerText = text.toLowerCase()
  const threats: string[] = []
  let scoreContribution = 0

  Object.entries(scamKeywords).forEach(([category, keywords]) => {
    const matches = keywords.filter(kw => lowerText.includes(kw))
    if (matches.length > 0) {
      threats.push(category)
      scoreContribution += 20
    }
  })

  let riskScore = Math.min(100, scoreContribution)
  const variance = (Math.random() - 0.5) * 20
  riskScore = Math.max(0, Math.min(100, riskScore + variance))

  const explanation = threats.length === 0
    ? 'This message does not contain obvious scam indicators.'
    : `Detected: ${threats.join(', ')}`

  return NextResponse.json({
    risk_score: Math.round(riskScore),
    threat_types: threats,
    explanation,
    confidence: Math.min(0.95, 0.6 + threats.length * 0.1),
  })
}
