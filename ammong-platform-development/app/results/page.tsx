'use client'

import { ArrowRight, GraduationCap, X, Check } from 'lucide-react'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

const mockAnalysis = {
  whatYouHave: [
    { skill: 'Java', status: 'match' },
    { skill: 'Python', status: 'match' },
    { skill: 'SQL', status: 'match' },
    { skill: 'Git', status: 'match' },
    { skill: 'REST APIs', status: 'match' },
    { skill: 'Spring Boot', status: 'partial' },
  ],
  whatJobRequires: [
    'Java',
    'SQL',
    'Git',
    'Spring Boot',
    'Docker',
    'AWS',
    'System Design',
  ],
  skillGaps: [
    { skill: 'Docker', priority: 1 },
    { skill: 'AWS', priority: 2 },
    { skill: 'System Design', priority: 3 },
  ],
  strongMatches: ['Java', 'SQL', 'Git'],
}

export default function ResultsPage() {
  const router = useRouter()
  const [target] = useState(() => {
    if (typeof window === 'undefined') return { company: 'Google', role: 'Backend Developer' }
    const params = new URLSearchParams(window.location.search)
    return {
      company: params.get('company') || 'Google',
      role: params.get('role') || 'Backend Developer',
    }
  })

  const company = target.company
  const role = target.role
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <main className="min-h-screen bg-[#fbfaf7] text-[#10213f]">
      <header className="border-b border-[#e7e5df] bg-[#fbfaf7]/90 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <button onClick={() => router.push('/')} className="flex items-center gap-2.5">
            <span className="grid size-9 place-items-center rounded-xl bg-[#0c244d] text-white">
              <GraduationCap size={18} />
            </span>
            <span className="text-[17px] font-bold tracking-[0.2em] text-[#0c244d]">AMMONG</span>
          </button>
          <nav className="hidden items-center gap-6 md:flex text-sm font-medium">
            <button onClick={() => setActiveTab('overview')} className={`${activeTab === 'overview' ? 'text-[#0c244d]' : 'text-slate-600'} hover:text-blue-700`}>Overview</button>
            <button onClick={() => setActiveTab('comparison')} className={`${activeTab === 'comparison' ? 'text-[#0c244d]' : 'text-slate-600'} hover:text-blue-700`}>Comparison</button>
            <button onClick={() => setActiveTab('weaknesses')} className={`${activeTab === 'weaknesses' ? 'text-[#0c244d]' : 'text-slate-600'} hover:text-blue-700`}>Resume</button>
            <button onClick={() => setActiveTab('plan')} className={`${activeTab === 'plan' ? 'text-[#0c244d]' : 'text-slate-600'} hover:text-blue-700`}>Plan</button>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:px-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[#0c244d]">
            Your AMMONG Analysis
          </h1>
          <div className="mt-4 flex flex-col gap-1 text-sm text-slate-600">
            <p>Target Company: <span className="font-semibold text-slate-900">{company}</span></p>
            <p>Target Role: <span className="font-semibold text-slate-900">{role}</span></p>
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Match Card */}
            <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-blue-50 to-white p-8">
              <div className="flex flex-col items-center justify-center text-center">
                <p className="text-sm font-semibold uppercase tracking-[0.14em] text-blue-700">Your Profile</p>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-5xl font-bold text-[#0c244d]">72%</span>
                  <span className="text-lg text-slate-600">Match</span>
                </div>
                <p className="mt-4 max-w-md text-sm leading-6 text-slate-600">
                  Based on the overlap between your analyzed profile and relevant job requirements.
                </p>
              </div>
            </div>

            {/* What You Have */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8">
              <h2 className="text-lg font-semibold text-[#0c244d] mb-6">What You Have</h2>
              <div className="grid gap-3">
                {mockAnalysis.whatYouHave.map((item) => (
                  <div key={item.skill} className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4">
                    <div className={`flex size-5 items-center justify-center rounded ${
                      item.status === 'match' ? 'bg-emerald-100 text-emerald-700' :
                      item.status === 'partial' ? 'bg-amber-100 text-amber-700' :
                      'bg-slate-200 text-slate-600'
                    }`}>
                      {item.status === 'match' ? '✓' : item.status === 'partial' ? '~' : '✕'}
                    </div>
                    <span className="text-sm font-medium text-slate-900">{item.skill}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* What Job Requires */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8">
              <h2 className="text-lg font-semibold text-[#0c244d] mb-6">What The Job Requires</h2>
              <div className="grid gap-3">
                {mockAnalysis.whatJobRequires.map((skill) => (
                  <div key={skill} className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4">
                    <span className="text-sm font-medium text-slate-900">{skill}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Your Skill Gaps */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8">
              <h2 className="text-lg font-semibold text-[#0c244d] mb-6">Your Skill Gaps</h2>
              <div className="grid gap-3 mb-8">
                {mockAnalysis.skillGaps.map((item) => (
                  <div key={item.skill} className="flex items-center gap-3 rounded-lg border border-red-100 bg-red-50 p-4">
                    <div className="flex size-5 items-center justify-center rounded bg-red-100 text-red-700">
                      ✕
                    </div>
                    <span className="text-sm font-medium text-slate-900">{item.skill}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900">Your Top Priorities</h3>
                {mockAnalysis.skillGaps.map((item, index) => (
                  <div key={item.skill} className="flex gap-4">
                    <div className="flex size-6 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700 flex-shrink-0">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{item.skill}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button onClick={() => setActiveTab('comparison')} className="flex-1 bg-[#0c244d] hover:bg-[#173766]">
                View Comparison <ArrowRight data-icon="inline-end" />
              </Button>
            </div>
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === 'comparison' && (
          <div className="space-y-8">
            <div className="rounded-2xl border border-slate-200 bg-white p-8">
              <h2 className="text-lg font-semibold text-[#0c244d] mb-8">What They Want vs What You Have</h2>
              <p className="mb-8 text-sm text-slate-600">Compare your current profile with the requirements identified for your target role.</p>

              <div className="grid gap-8 lg:grid-cols-2">
                {/* Left Column */}
                <div>
                  <h3 className="mb-4 font-semibold text-slate-900">Job Requirements</h3>
                  <div className="space-y-2">
                    {mockAnalysis.whatJobRequires.map((skill) => (
                      <div key={skill} className="text-sm text-slate-700 py-2 px-3 rounded-lg bg-slate-50">
                        {skill}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right Column */}
                <div>
                  <h3 className="mb-4 font-semibold text-slate-900">Your Profile</h3>
                  <div className="space-y-2">
                    {mockAnalysis.whatYouHave.map((item) => (
                      <div key={item.skill} className="flex items-center gap-2 text-sm py-2 px-3 rounded-lg bg-slate-50">
                        <span className={item.status === 'match' ? 'text-emerald-600' : item.status === 'partial' ? 'text-amber-600' : 'text-red-600'}>
                          {item.status === 'match' ? '✓' : item.status === 'partial' ? '~' : '✕'}
                        </span>
                        <span className="text-slate-700">{item.skill}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8 border-t border-slate-200 pt-6">
                <p className="text-sm text-slate-600 mb-6">
                  <span className="font-semibold text-slate-900">3</span> important skills are currently missing or not demonstrated.
                </p>

                <div className="grid gap-8 lg:grid-cols-2">
                  <div>
                    <h4 className="font-semibold text-emerald-700 mb-3">Your strongest matches</h4>
                    <div className="space-y-2">
                      {mockAnalysis.strongMatches.map((skill) => (
                        <div key={skill} className="flex items-center gap-2 text-sm text-slate-700">
                          <span className="text-emerald-600">✓</span>
                          {skill}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-red-700 mb-3">Your biggest gaps</h4>
                    <div className="space-y-2">
                      {mockAnalysis.skillGaps.map((item) => (
                        <div key={item.skill} className="flex items-center gap-2 text-sm text-slate-700">
                          <span className="text-red-600">✕</span>
                          {item.skill}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button onClick={() => setActiveTab('plan')} className="flex-1 bg-[#0c244d] hover:bg-[#173766]">
                Build Improvement Plan <ArrowRight data-icon="inline-end" />
              </Button>
            </div>
          </div>
        )}

        {/* Weaknesses Tab */}
        {activeTab === 'weaknesses' && (
          <div className="space-y-8">
            <div className="rounded-2xl border border-slate-200 bg-white p-8">
              <h2 className="text-lg font-semibold text-[#0c244d] mb-4">Resume Weaknesses</h2>
              <p className="text-sm text-slate-600 mb-8">Areas of your resume that could be improved for your target role.</p>

              <div className="space-y-6">
                {[
                  {
                    title: 'Project Descriptions',
                    problem: 'Your projects list technologies but do not clearly explain outcomes or impact.',
                    suggestion: 'Add measurable results and business impact for each project.',
                  },
                  {
                    title: 'Technical Evidence',
                    problem: 'Some listed skills are not strongly supported by project or experience evidence.',
                    suggestion: 'Link each skill to specific projects or work experience that demonstrates it.',
                  },
                  {
                    title: 'Role Alignment',
                    problem: 'Your resume could emphasize skills more relevant to your target role.',
                    suggestion: 'Reorder skills section to highlight Docker, AWS, and System Design.',
                  },
                  {
                    title: 'Achievements',
                    problem: 'Add measurable results where possible instead of only describing responsibilities.',
                    suggestion: 'Convert responsibility statements to achievement statements with metrics.',
                  },
                ].map((item) => (
                  <div key={item.title} className="rounded-xl border border-slate-200 bg-slate-50 p-6">
                    <h3 className="font-semibold text-[#0c244d] mb-2">{item.title}</h3>
                    <p className="text-sm text-slate-600 mb-3">{item.problem}</p>
                    <p className="text-sm font-medium text-blue-700">Suggested: {item.suggestion}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button onClick={() => setActiveTab('plan')} className="flex-1 bg-[#0c244d] hover:bg-[#173766]">
                View Improvement Plan <ArrowRight data-icon="inline-end" />
              </Button>
            </div>
          </div>
        )}

        {/* Plan Tab */}
        {activeTab === 'plan' && (
          <div className="space-y-8">
            <div className="rounded-2xl border border-slate-200 bg-white p-8">
              <h2 className="text-lg font-semibold text-[#0c244d] mb-4">Your Improvement Plan</h2>
              <p className="text-sm text-slate-600 mb-8">Focus on the areas that can strengthen your profile for your target role.</p>

              <div className="space-y-8 mb-12">
                {[
                  {
                    priority: 1,
                    skill: 'Docker',
                    why: 'Required by relevant backend job requirements and not currently demonstrated.',
                    action: 'Learn Docker fundamentals and containerize one backend project.',
                  },
                  {
                    priority: 2,
                    skill: 'AWS',
                    why: 'Cloud skills appear in relevant job requirements and are not currently demonstrated.',
                    action: 'Learn AWS fundamentals and deploy a small project.',
                  },
                  {
                    priority: 3,
                    skill: 'System Design',
                    why: 'Your profile currently provides limited evidence of system design knowledge.',
                    action: 'Learn APIs, databases, caching and basic scalability concepts.',
                  },
                ].map((item) => (
                  <div key={item.skill} className="rounded-xl border border-slate-200 bg-slate-50 p-6">
                    <div className="flex items-start gap-4">
                      <div className="flex size-8 items-center justify-center rounded-full bg-blue-600 text-white font-bold flex-shrink-0">
                        {item.priority}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-[#0c244d] mb-2">{item.skill}</h3>
                        <div className="space-y-2">
                          <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase">Why:</p>
                            <p className="text-sm text-slate-700">{item.why}</p>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase">Action:</p>
                            <p className="text-sm text-slate-700">{item.action}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t border-slate-200 pt-8">
                <h3 className="font-semibold text-[#0c244d] mb-4">Resume Improvements</h3>
                <ul className="space-y-3">
                  {[
                    'Strengthen project descriptions',
                    'Add measurable achievements',
                    'Highlight relevant technical skills',
                    'Add stronger project evidence',
                    'Mention deployment experience where applicable',
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-3 text-sm text-slate-700">
                      <span className="text-emerald-600 font-bold flex-shrink-0">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button onClick={() => router.push('/analyze')} className="flex-1 bg-[#0c244d] hover:bg-[#173766]">
                Update Profile & Analyze Again <ArrowRight data-icon="inline-end" />
              </Button>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}
