'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Upload, Mic } from 'lucide-react'

interface AudioAnalyzerProps {
  onAnalyze: (file: File) => void
  isLoading: boolean
}

export default function AudioAnalyzer({ onAnalyze, isLoading }: AudioAnalyzerProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  const handleFileSelect = (file: File) => {
    if (file.type.startsWith('audio/')) {
      setSelectedFile(file)
    } else {
      alert('Please select an audio file')
    }
  }

  const handleAnalyze = () => {
    if (selectedFile) {
      onAnalyze(selectedFile)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      
      const chunks: Blob[] = []
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data)
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const file = new File([blob], 'recording.webm', { type: 'audio/webm' })
        setSelectedFile(file)
      }
      
      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      alert('Cannot access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
    }
  }

  return (
    <Card className="p-6 space-y-4">
      <div className="space-y-4">
        <div>
          <label className="text-sm font-semibold text-foreground mb-3 block">
            Upload or record audio
          </label>
          
          {/* Upload Button */}
          <div className="mb-4">
            <input
              type="file"
              ref={fileInputRef}
              accept="audio/*"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  handleFileSelect(e.target.files[0])
                }
              }}
              className="hidden"
              disabled={isLoading || isRecording}
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              className="w-full"
              disabled={isLoading || isRecording}
            >
              <Upload className="w-4 h-4 mr-2" />
              Choose Audio File
            </Button>
          </div>

          {/* Recording Button */}
          <Button
            onClick={isRecording ? stopRecording : startRecording}
            className="w-full"
            variant={isRecording ? 'destructive' : 'default'}
            disabled={isLoading}
          >
            <Mic className="w-4 h-4 mr-2" />
            {isRecording ? 'Stop Recording' : 'Record Audio'}
          </Button>
        </div>

        {/* File Info */}
        {selectedFile && (
          <div className="bg-muted/50 rounded p-3 text-sm">
            <p className="font-medium text-foreground">Selected file:</p>
            <p className="text-muted-foreground">
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          </div>
        )}

        {isRecording && (
          <div className="bg-accent/10 border border-accent rounded p-3 text-sm">
            <p className="text-accent font-medium flex items-center gap-2">
              <span className="w-2 h-2 bg-accent rounded-full animate-pulse"></span>
              Recording...
            </p>
          </div>
        )}
      </div>

      <Button
        onClick={handleAnalyze}
        disabled={!selectedFile || isLoading || isRecording}
        className="w-full bg-primary hover:bg-primary/90"
      >
        {isLoading ? (
          <>
            <Spinner className="w-4 h-4 mr-2" />
            Analyzing...
          </>
        ) : (
          'Analyze Audio'
        )}
      </Button>

      <p className="text-xs text-muted-foreground text-center">
        Your audio is processed privately. Nothing is stored or shared.
      </p>
    </Card>
  )
}
