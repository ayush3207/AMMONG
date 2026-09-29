'use client'

import { ArrowRight, GraduationCap, Upload, X } from 'lucide-react'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export default function AnalyzePage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [company, setCompany] = useState('')
  const [jobRole, setJobRole] = useState('')
  const [loading, setLoading] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.add('border-blue-400', 'bg-blue-50')
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50')
    if (e.dataTransfer.files?.[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleAnalyze = async () => {
    if (!file || !company || !jobRole) {
      alert('Please fill in all fields')
      return
    }

    setLoading(true)
    // Simulate processing
    setTimeout(() => {
      router.push(`/processing?company=${encodeURIComponent(company)}&role=${encodeURIComponent(jobRole)}`)
    }, 500)
  }

  return (
    <main className="min-h-screen bg-[#fbfaf7] text-[#10213f]">
      <header className="border-b border-[#e7e5df] bg-[#fbfaf7]/90 backdrop-blur">
        <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <button onClick={() => router.push('/')} className="flex items-center gap-2.5" aria-label="AMMONG home">
            <span className="grid size-9 place-items-center rounded-xl bg-[#0c244d] text-white">
              <GraduationCap size={18} />
            </span>
            <span className="text-[17px] font-bold tracking-[0.2em] text-[#0c244d]">AMMONG</span>
          </button>
          <nav className="hidden items-center gap-6 md:flex">
            <button onClick={() => router.push('/')} className="text-sm font-medium text-slate-600 hover:text-blue-700">Home</button>
            <button onClick={() => router.push('/#how-it-works')} className="text-sm font-medium text-slate-600 hover:text-blue-700">How it works</button>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-5 py-16 sm:px-8 lg:px-10 lg:py-24">
        <div className="mb-12 text-center">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[#0c244d] sm:text-4xl">
            Analyze Your Placement Readiness
          </h1>
          <p className="mt-4 text-base leading-7 text-slate-600">
            Upload your resume and tell AMMONG what job you&apos;re targeting.
          </p>
        </div>

        <div className="space-y-8">
          {/* Resume Upload */}
          <div>
            <label className="mb-3 block text-sm font-semibold text-[#0c244d]">Resume Upload</label>
            {!file ? (
              <label
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className="block cursor-pointer rounded-2xl border-2 border-dashed border-slate-200 bg-white p-8 transition-colors hover:border-blue-300 hover:bg-blue-50"
              >
                <div className="flex flex-col items-center gap-2">
                  <Upload size={32} className="text-slate-400" />
                  <p className="text-sm font-semibold text-slate-700">Upload your resume</p>
                  <p className="text-xs text-slate-500">PDF format</p>
                </div>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="grid size-10 place-items-center rounded-lg bg-blue-50">
                      <Upload size={20} className="text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-700">{file.name}</p>
                      <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setFile(null)}
                    className="rounded-lg p-2 hover:bg-slate-100"
                  >
                    <X size={18} className="text-slate-400" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Target Company */}
          <div>
            <label htmlFor="company" className="mb-3 block text-sm font-semibold text-[#0c244d]">
              Target Company
            </label>
            <input
              id="company"
              type="text"
              placeholder="e.g. Google, Microsoft, TCS"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
            />
          </div>

          {/* Target Job Role */}
          <div>
            <label htmlFor="role" className="mb-3 block text-sm font-semibold text-[#0c244d]">
              Target Job Role
            </label>
            <input
              id="role"
              type="text"
              placeholder="e.g. Software Engineer, Backend Developer"
              value={jobRole}
              onChange={(e) => setJobRole(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
            />
          </div>

          {/* Note */}
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-sm text-slate-700">
              <span className="font-semibold text-blue-700">AMMONG</span> compares your profile with relevant job requirements and identifies what you should improve.
            </p>
          </div>

          {/* CTA Button */}
          <div className="pt-4">
            <Button
              onClick={handleAnalyze}
              disabled={loading || !file || !company || !jobRole}
              size="lg"
              className="w-full h-12 bg-[#0c244d] hover:bg-[#173766] disabled:opacity-50"
            >
              {loading ? 'Analyzing...' : 'Analyze My Profile'}
              {!loading && <ArrowRight data-icon="inline-end" />}
            </Button>
          </div>
        </div>
      </section>
    </main>
  )
}
