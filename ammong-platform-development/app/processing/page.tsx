'use client'

import { GraduationCap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const steps = [
  'Reading your resume',
  'Identifying your skills and experience',
  'Analyzing job requirements',
  'Finding your skill gaps',
]

export default function ProcessingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    // Simulate processing steps
    const intervals = steps.map((_, index) => {
      return setTimeout(() => {
        setCurrentStep(index + 1)
      }, (index + 1) * 800)
    })

    // Navigate to results after all steps
    const finalTimeout = setTimeout(() => {
      const params = new URLSearchParams(window.location.search)
      const company = params.get('company') || 'Google'
      const role = params.get('role') || 'Backend Developer'
      router.push(`/results?company=${encodeURIComponent(company)}&role=${encodeURIComponent(role)}`)
    }, steps.length * 800 + 500)

    return () => {
      intervals.forEach(clearTimeout)
      clearTimeout(finalTimeout)
    }
  }, [router])

  return (
    <main className="min-h-screen bg-[#fbfaf7] text-[#10213f]">
      <header className="border-b border-[#e7e5df] bg-[#fbfaf7]/90 backdrop-blur">
        <div className="mx-auto flex h-[76px] max-w-7xl items-center px-5 sm:px-8 lg:px-10">
          <button onClick={() => router.push('/')} className="flex items-center gap-2.5">
            <span className="grid size-9 place-items-center rounded-xl bg-[#0c244d] text-white">
              <GraduationCap size={18} />
            </span>
            <span className="text-[17px] font-bold tracking-[0.2em] text-[#0c244d]">AMMONG</span>
          </button>
        </div>
      </header>

      <section className="flex min-h-[calc(100vh-76px)] flex-col items-center justify-center px-5 sm:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[#0c244d] sm:text-4xl">
            AMMONG is analyzing your profile...
          </h1>
          <p className="mt-4 text-base text-slate-600">
            This usually takes a few seconds.
          </p>
        </div>

        <div className="mt-12 space-y-4 w-full max-w-md">
          {steps.map((step, index) => (
            <div key={step} className="flex items-center gap-3">
              <div className={`flex size-6 items-center justify-center rounded-full ${
                index < currentStep
                  ? 'bg-emerald-500 text-white'
                  : index === currentStep
                    ? 'bg-blue-500 text-white'
                    : 'bg-slate-200'
              }`}>
                {index < currentStep ? (
                  <span className="text-sm font-bold">✓</span>
                ) : index === currentStep ? (
                  <span className="inline-block size-2 rounded-full bg-white animate-pulse" />
                ) : (
                  <span className="text-xs font-semibold text-slate-500">{index + 1}</span>
                )}
              </div>
              <p className={`text-sm font-medium ${
                index < currentStep
                  ? 'text-slate-600'
                  : index === currentStep
                    ? 'text-[#0c244d]'
                    : 'text-slate-400'
              }`}>
                {step}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-12 w-full max-w-md">
          <div className="h-1 w-full rounded-full bg-slate-200 overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-500"
              style={{ width: `${(currentStep / steps.length) * 100}%` }}
            />
          </div>
        </div>
      </section>
    </main>
  )
}
