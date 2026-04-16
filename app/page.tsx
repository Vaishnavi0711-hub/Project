'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Shield, Zap, Lock } from 'lucide-react'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary" />
            <span className="text-2xl font-bold text-primary">TRUST.AI</span>
          </div>
          <nav className="hidden md:flex gap-8 text-sm font-medium">
            <Link href="#features" className="hover:text-primary transition">Features</Link>
            <Link href="#how-it-works" className="hover:text-primary transition">How It Works</Link>
            <Link href="#safety" className="hover:text-primary transition">Safety</Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground leading-tight">
            <span className="text-primary">Protect</span> yourself from scams with AI
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            TRUST.AI analyzes text messages and voice calls in real-time to detect scams, protect your identity, and keep your finances safe. No data stored. Complete privacy.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto bg-primary hover:bg-primary/90">
                Analyze Now
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-muted/30 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Powerful Detection Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-card rounded-lg border border-border p-8 space-y-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Text Analysis</h3>
              <p className="text-muted-foreground">
                AI-powered detection of phishing messages, fake urgency tactics, and suspicious links in SMS and text.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-card rounded-lg border border-border p-8 space-y-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Voice Detection</h3>
              <p className="text-muted-foreground">
                Analyze audio calls for deepfake voices, spoofing attempts, and suspicious patterns in real-time.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-card rounded-lg border border-border p-8 space-y-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <Lock className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Privacy First</h3>
              <p className="text-muted-foreground">
                Your data is never stored. Analysis happens locally. Complete privacy protection without tracking.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">How TRUST.AI Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="text-4xl font-bold text-primary">1</div>
              <h3 className="text-xl font-semibold">Upload Content</h3>
              <p className="text-muted-foreground">
                Paste a message or upload an audio file for analysis
              </p>
            </div>
            <div className="text-center space-y-4">
              <div className="text-4xl font-bold text-primary">2</div>
              <h3 className="text-xl font-semibold">AI Analysis</h3>
              <p className="text-muted-foreground">
                Our neural networks analyze for scam indicators
              </p>
            </div>
            <div className="text-center space-y-4">
              <div className="text-4xl font-bold text-primary">3</div>
              <h3 className="text-xl font-semibold">Get Risk Score</h3>
              <p className="text-muted-foreground">
                Receive instant risk assessment with clear explanations
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-primary-foreground py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-3xl font-bold">Ready to protect yourself?</h2>
          <p className="text-lg opacity-90">
            Start analyzing suspicious messages and calls right now, completely free
          </p>
          <Link href="/dashboard">
            <Button size="lg" className="bg-primary-foreground text-primary hover:bg-primary-foreground/90">
              Launch Dashboard
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 bg-muted/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-muted-foreground">
          <p>© 2026 TRUST.AI - Privacy-first scam detection powered by AI</p>
        </div>
      </footer>
    </main>
  )
}
