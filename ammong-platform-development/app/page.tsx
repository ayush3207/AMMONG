'use client'

import {
  ArrowRight,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  CircleCheck,
  FileText,
  Github,
  GraduationCap,
  Map,
  Menu,
  Search,
  Sparkles,
  Target,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'

const insights = [
  { icon: BriefcaseBusiness, title: 'Job Match', text: 'Understand which roles fit your current profile.', accent: 'bg-blue-50 text-blue-700' },
  { icon: Target, title: 'Skill Gap', text: 'See exactly which required skills you are missing.', accent: 'bg-amber-50 text-amber-700' },
  { icon: BarChart3, title: 'Placement Readiness', text: 'Understand your current preparation level.', accent: 'bg-emerald-50 text-emerald-700' },
  { icon: Map, title: 'Learning Roadmap', text: 'Get actionable next steps based on your target role.', accent: 'bg-violet-50 text-violet-700' },
]

const steps = [
  ['01', 'Build Your Profile', 'Resume, skills, projects and GitHub'],
  ['02', 'Analyze Your Skills', 'AI identifies skills and project evidence'],
  ['03', 'Compare With Jobs', 'Match your profile against job requirements'],
  ['04', 'Improve Your Profile', 'Get skill gaps and a personalized roadmap'],
]

function ProductFlow() {
  const nodes = [
    { icon: GraduationCap, label: 'Student Profile', detail: 'Resume · Projects · GitHub' },
    { icon: Sparkles, label: 'AI Analysis', detail: 'Skills & evidence found' },
    { icon: BriefcaseBusiness, label: 'Job Match', detail: '86% fit for 24 roles' },
    { icon: Target, label: 'Skill Gap', detail: '4 priority skills' },
    { icon: BookOpen, label: 'Learning Roadmap', detail: '6 week action plan' },
  ]
  return (
    <div className="relative mx-auto w-full max-w-[500px] rounded-[24px] border border-slate-200 bg-white p-4 shadow-[0_24px_70px_-28px_rgba(15,35,75,0.45)] sm:p-5">
      <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-4">
        <div><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600">Profile intelligence</p><p className="mt-1 text-sm font-semibold text-slate-900">Your placement journey</p></div>
        <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-700"><span className="size-1.5 rounded-full bg-emerald-500" />Live analysis</span>
      </div>
      <div className="flex flex-col gap-2.5">
        {nodes.map(({ icon: Icon, label, detail }, index) => (
          <div key={label} className="flex items-center gap-3">
            <div className={`grid size-10 shrink-0 place-items-center rounded-xl ${index === 0 ? 'bg-[#0c244d] text-white' : 'bg-blue-50 text-blue-700'}`}><Icon size={17} /></div>
            <div className="min-w-0 flex-1 rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2.5"><p className="text-xs font-semibold text-slate-800">{label}</p><p className="mt-0.5 text-[11px] text-slate-500">{detail}</p></div>
            {index < 4 && <ChevronRight className="text-slate-300" size={15} />}
          </div>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 border-t border-slate-100 pt-4"><div><p className="text-[10px] text-slate-400">Readiness</p><p className="mt-1 text-lg font-bold text-slate-900">78%</p></div><div><p className="text-[10px] text-slate-400">Matched roles</p><p className="mt-1 text-lg font-bold text-slate-900">24</p></div><div><p className="text-[10px] text-slate-400">Skills found</p><p className="mt-1 text-lg font-bold text-slate-900">14</p></div></div>
    </div>
  )
}

export default function Page() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const scrollTo = (id: string) => { document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); setMobileOpen(false) }
  return (
    <main className="min-h-screen overflow-hidden bg-[#fbfaf7] text-[#10213f]">
      <header className="relative z-20 border-b border-[#e7e5df] bg-[#fbfaf7]/90 backdrop-blur">
        <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <button onClick={() => scrollTo('top')} className="flex items-center gap-2.5" aria-label="AMMONG home"><span className="grid size-9 place-items-center rounded-xl bg-[#0c244d] text-white"><GraduationCap size={18} /></span><span className="text-[17px] font-bold tracking-[0.2em] text-[#0c244d]">AMMONG</span></button>
          <nav className={`${mobileOpen ? 'absolute left-0 right-0 top-[76px] flex border-b border-slate-200 bg-[#fbfaf7] p-5 shadow-lg' : 'hidden'} flex-col gap-5 text-sm font-medium text-slate-600 md:static md:flex md:flex-row md:items-center md:border-0 md:bg-transparent md:p-0 md:shadow-none`}><button onClick={() => scrollTo('how-it-works')} className="text-left hover:text-blue-700">How it works</button><button onClick={() => scrollTo('insights')} className="text-left hover:text-blue-700">Insights</button><button onClick={() => scrollTo('about')} className="text-left hover:text-blue-700">About AMMONG</button><a href="/analyze" className="w-full md:hidden"><Button className="w-full bg-[#0c244d] hover:bg-[#173766]">Analyze My Profile</Button></a></nav>
          <div className="hidden items-center gap-6 md:flex"><button onClick={() => scrollTo('insights')} className="text-sm font-medium text-slate-600 hover:text-blue-700">Explore Jobs</button><a href="/analyze"><Button className="bg-[#0c244d] px-5 hover:bg-[#173766]">Analyze My Profile <ArrowRight data-icon="inline-end" /></Button></a></div>
          <button className="md:hidden" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle menu">{mobileOpen ? <X /> : <Menu />}</button>
        </div>
      </header>

      <section id="top" className="relative mx-auto grid max-w-7xl gap-12 px-5 pb-20 pt-16 sm:px-8 sm:pt-24 lg:grid-cols-[1.02fr_0.98fr] lg:items-center lg:gap-16 lg:px-10 lg:pb-28">
        <div className="relative z-10"><div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-blue-700"><span className="size-1.5 rounded-full bg-blue-600" />Placement intelligence for students</div><h1 className="max-w-[650px] text-[clamp(3rem,6vw,5.7rem)] font-semibold leading-[0.98] tracking-[-0.065em] text-[#0c244d]">Know what you have.<br /><span className="text-blue-600">Know what you&apos;re missing.</span></h1><p className="mt-7 max-w-[560px] text-base leading-7 text-slate-600 sm:text-lg">AMMONG analyzes your resume, skills, projects and GitHub profile against real job requirements to identify your job match, skill gaps and next learning steps.</p>              <div className="mt-9 flex flex-col gap-3 sm:flex-row"><a href="/analyze" className="flex-1 sm:flex-none"><Button size="lg" className="w-full h-12 bg-[#0c244d] px-6 hover:bg-[#173766]">Analyze My Profile <ArrowRight data-icon="inline-end" /></Button></a><Button onClick={() => scrollTo('insights')} size="lg" variant="outline" className="h-12 border-slate-300 bg-transparent px-6 text-[#0c244d] hover:bg-white">Explore Jobs <BriefcaseBusiness data-icon="inline-end" /></Button></div><div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-500"><span className="flex items-center gap-1.5"><CircleCheck className="text-emerald-600" size={15} />Built around real requirements</span><span className="flex items-center gap-1.5"><CircleCheck className="text-emerald-600" size={15} />Made for your next role</span></div></div>
        <div className="relative"><div className="absolute -right-20 -top-28 size-80 rounded-full bg-blue-100/50 blur-3xl" /><ProductFlow /></div>
      </section>

      <section id="about" className="border-y border-[#e7e5df] bg-[#f4f6f8] px-5 py-10 sm:px-8 lg:px-10"><div className="mx-auto flex max-w-7xl flex-col gap-7 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-xs"><p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600">Grounded in evidence</p><h2 className="mt-2 text-xl font-semibold tracking-tight text-[#0c244d]">Built around real job requirements</h2></div><div className="grid flex-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 lg:pl-20">{[['01', 'Job postings', BriefcaseBusiness], ['02', 'Required skills', Check], ['03', 'Student profiles', GraduationCap], ['04', 'Project evidence', FileText]].map(([num, label, Icon]) => <div key={label as string} className="flex items-center gap-3 border-l border-slate-200 pl-4"><span className="text-[10px] font-bold text-blue-600">{num}</span><Icon className="text-slate-500" size={17} /><span className="text-sm font-medium text-slate-700">{label as string}</span></div>)}</div></div></section>

      <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-10 lg:py-28"><div className="max-w-2xl"><p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600">A clearer path forward</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-[#0c244d] sm:text-4xl">How AMMONG Works</h2><p className="mt-4 text-base leading-7 text-slate-600">Turn everything you&apos;ve built into a practical plan for the roles you want.</p></div><div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">{steps.map(([number, title, text]) => <div key={number} className="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"><span className="text-sm font-bold text-blue-600">{number}</span><div className="mt-16"><h3 className="text-base font-semibold text-[#0c244d]">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{text}</p></div></div>)}</div></section>

      <section id="insights" className="bg-[#0c244d] px-5 py-20 text-white sm:px-8 lg:px-10 lg:py-28"><div className="mx-auto max-w-7xl"><div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-end"><div><p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-300">From one profile</p><h2 className="mt-3 max-w-lg text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">One Platform. Four Placement Insights.</h2></div><p className="max-w-sm text-sm leading-6 text-blue-100/70">Know where you stand today and exactly what to do next.</p></div><div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">{insights.map(({ icon: Icon, title, text, accent }) => <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.06] p-6"><span className={`grid size-11 place-items-center rounded-xl ${accent}`}><Icon size={20} /></span><h3 className="mt-12 text-base font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-blue-100/65">{text}</p></div>)}</div></div></section>

      <section id="analyze" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-10 lg:py-28"><div className="relative overflow-hidden rounded-[28px] bg-[#e9f0fb] px-6 py-12 sm:px-12 lg:flex lg:items-center lg:justify-between lg:px-16"><div className="absolute -right-16 -top-20 size-64 rounded-full border-[32px] border-blue-200/40" /><div className="relative"><p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-700">Your next opportunity starts here</p><h2 className="mt-3 max-w-xl text-3xl font-semibold tracking-[-0.045em] text-[#0c244d] sm:text-4xl">Start Your Placement Analysis</h2><p className="mt-4 max-w-lg text-sm leading-6 text-slate-600">Build a profile that tells you more than where you are. AMMONG shows you where you can go next.</p></div><a href="/analyze" className="relative mt-8 inline-block"><Button size="lg" className="h-12 bg-[#0c244d] px-6 hover:bg-[#173766] lg:mt-0">Analyze My Profile <ArrowRight data-icon="inline-end" /></Button></a></div></section>
      <footer className="border-t border-[#e7e5df] px-5 py-7 sm:px-8 lg:px-10"><div className="mx-auto flex max-w-7xl flex-col gap-3 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between"><span className="font-semibold tracking-[0.18em] text-[#0c244d]">AMMONG</span><span>Placement intelligence for the next generation.</span><span>© 2026 AMMONG</span></div></footer>
    </main>
  )
}

