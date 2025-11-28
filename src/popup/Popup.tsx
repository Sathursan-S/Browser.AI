import { useMemo, useState } from 'react'

type PanelView = 'tasks' | 'history'

const taskSteps = [
  'Starting your automation task',
  'Processing step 1',
  'Processing step 2',
  'Processing step 3',
  'Processing step 4',
]

const historyItems = [
  { title: 'Play latest Tamil movie', timestamp: 'Today · 09:34 AM' },
  { title: 'Collect pricing for laptops', timestamp: 'Yesterday · 08:12 PM' },
  { title: 'Summarize meeting transcript', timestamp: 'Yesterday · 04:45 PM' },
]

const IconButton = ({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  onClick?: () => void
}) => (
  <button
    onClick={onClick}
    title={label}
    className="h-9 w-9 inline-flex items-center justify-center rounded-full bg-white/30 text-slate-700 hover:bg-white/70 transition-colors"
  >
    {icon}
  </button>
)

const Dot = () => <span className="h-2 w-2 rounded-full bg-green-400" />

export const Popup = () => {
  const [panel, setPanel] = useState<PanelView>('tasks')
  const [showMenu, setShowMenu] = useState(false)
  const [message, setMessage] = useState('')

  const panelTitle = useMemo(() => (panel === 'history' ? 'History' : 'Play latest Tamil movie'), [panel])
  const panelSubtitle = useMemo(() => (panel === 'history' ? 'Recent automations' : 'Task running...'), [panel])

  return (
    <main className="w-[360px] h-[600px] bg-[#f4f6ff] text-[#1e1b4b] font-['Inter',_system-ui]">
      <div className="h-full flex flex-col px-4 py-3 gap-3">
        <header className="relative rounded-2xl bg-gradient-to-b from-[#c5d2ff] to-[#b3c2ff] px-4 py-3 flex items-center justify-between shadow-sm border border-white/40">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-white/70 border border-white/60 flex items-center justify-center text-sm font-semibold text-[#4c4fb5]">
              Bz
            </div>
            <div>
              <p className="text-sm font-medium text-[#4b4f74]">Browze.AI</p>
              <div className="flex items-center gap-1 text-xs text-[#6d739c]">
                <Dot />
                <span>Assistant ready</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <IconButton
              icon={
                <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <path d="M10 4a6 6 0 0 0-2 11.65V18h4v-2.35A6 6 0 0 0 10 4Z" />
                </svg>
              }
              label="History"
              onClick={() => {
                setPanel('history')
                setShowMenu(false)
              }}
            />
            <IconButton
              icon={
                <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <path d="M10 2v16M2 10h16" strokeLinecap="round" />
                </svg>
              }
              label="New task"
              onClick={() => {
                setPanel('tasks')
                setShowMenu(false)
              }}
            />
            <button
              onClick={() => setShowMenu((prev) => !prev)}
              className="h-9 w-9 inline-flex items-center justify-center rounded-full bg-white/30 text-slate-700 hover:bg-white/70 transition-colors"
              title="Settings"
            >
              <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.6">
                <path
                  d="M11.5 2.3a1.5 1.5 0 0 0-3 0l-.14 1.13a5.92 5.92 0 0 0-1.82 1.05L5.3 3.7a1.5 1.5 0 0 0-2.12 2.12l.78 1.24c-.23.58-.37 1.2-.41 1.83L2.3 9.5a1.5 1.5 0 0 0 0 3l1.25.1c.04.63.18 1.25.41 1.83l-.78 1.24a1.5 1.5 0 1 0 2.12 2.12l1.24-.78c.57.23 1.19.37 1.82.41l.1 1.25a1.5 1.5 0 0 0 3 0l.1-1.25c.63-.04 1.25-.18 1.82-.41l1.24.78a1.5 1.5 0 0 0 2.12-2.12l-.78-1.24c.23-.58.37-1.2.41-1.83l1.25-.1a1.5 1.5 0 0 0 0-3l-1.25-.1a6.08 6.08 0 0 0-.41-1.83l.78-1.24a1.5 1.5 0 0 0-2.12-2.12l-1.24.78c-.57-.23-1.19-.37-1.82-.41Z"
                  strokeLinejoin="round"
                />
                <circle cx="10" cy="11" r="2.5" />
              </svg>
            </button>
          </div>
          {showMenu && (
            <div className="absolute right-2 top-14 w-32 rounded-2xl bg-white shadow-lg border border-slate-100 text-sm text-[#4b4f74] py-2">
              <button className="w-full text-left px-4 py-2 hover:bg-[#eef1ff]" onClick={() => setShowMenu(false)}>
                Settings
              </button>
              <button
                className="w-full text-left px-4 py-2 hover:bg-[#eef1ff]"
                onClick={() => {
                  setPanel('history')
                  setShowMenu(false)
                }}
              >
                History
              </button>
            </div>
          )}
        </header>

        <section className="flex-1 bg-white rounded-3xl shadow-inner border border-[#e3e9ff] p-4 flex flex-col">
          <div className="rounded-2xl border border-[#dcdff5] bg-[#eef1ff]">
            <div className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="text-sm font-medium text-[#4b4f74]">{panelTitle}</p>
                <p className="text-xs text-[#6d739c]">{panelSubtitle}</p>
              </div>
              <div className="flex gap-2">
                <span className="h-7 w-7 rounded-full border border-[#c4c8ef] flex items-center justify-center text-[#6d739c] text-sm">
                  ⟳
                </span>
                <span className="h-7 w-7 rounded-full border border-[#c4c8ef] flex items-center justify-center text-[#6d739c] text-sm">
                  ⓘ
                </span>
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto border-t border-[#dcdff5] bg-white rounded-b-2xl">
              {panel === 'history' ? (
                <ul className="divide-y divide-[#f0f2ff]">
                  {historyItems.map((item) => (
                    <li key={item.title} className="px-4 py-3">
                      <p className="text-sm font-medium text-[#4b4f74]">{item.title}</p>
                      <p className="text-xs text-[#8b90b8]">{item.timestamp}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <ol className="space-y-2 px-4 py-3">
                  {taskSteps.map((step, index) => (
                    <li key={step} className="flex gap-3 items-start text-sm text-[#4b4f74]">
                      <span className="mt-1 h-2.5 w-2.5 rounded-full border-2 border-[#4c4fb5] bg-white" />
                      <span>
                        Step {index + 1}: {step}
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
          <div className="mt-auto pt-4">
            <p className="text-xs text-[#8b90b8] mb-2">Assistant input</p>
            <div className="rounded-2xl bg-[#d6dcff] px-3 py-2 flex items-center gap-3">
              <input
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Type your message here..."
                className="flex-1 bg-transparent text-sm text-[#4b4f74] placeholder:text-[#7e84ac] focus:outline-none"
              />
              <div className="flex gap-2">
                <button className="h-10 w-10 rounded-2xl bg-white text-[#4c4fb5] shadow-sm border border-white/80 hover:scale-[1.02] transition-transform">
                  🎙️
                </button>
                <button
                  className="h-10 w-10 rounded-2xl bg-[#0f58f3] text-white shadow-lg hover:bg-[#1f66ff] transition-colors"
                  onClick={() => setMessage('')}
                >
                  ▶
                </button>
              </div>
            </div>
            <p className="text-xs text-[#8b90b8] mt-2">{message ? 'Ready to run' : 'Task running....'}</p>
          </div>
        </section>
      </div>
    </main>
  )
}

export default Popup
