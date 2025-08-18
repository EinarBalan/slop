import React, { useEffect, useMemo, useState } from 'react'

type Post = {
  title: string
  self_text: string
  subreddit?: string
  post_id?: string
  over_18?: string | boolean
  link_flair_text?: string
  is_ai?: boolean
}

type FeedResponse = {
  posts: Post[]
  count: number
  batchIndex: number
  skippedInvalidPosts: number
  totalProcessedRows: number
  endOfFile: boolean
  batchSize: number
  aiPostsCount: number
}

const prefersDark = () => window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches

export function App(): JSX.Element {
  const [feed, setFeed] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [theme, setTheme] = useState(prefersDark() ? 'dark' : 'light')
  const [openMenu, setOpenMenu] = useState<number | null>(null)
  const [votes, setVotes] = useState<Record<string, 'up' | 'down'>>({})
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [username, setUsername] = useState<string>(() => localStorage.getItem('username') || `user_${Math.floor(Math.random()*100000)}`)
  const [authError, setAuthError] = useState<string | null>(null)
  const [loggingIn, setLoggingIn] = useState(false)

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => setTheme(media.matches ? 'dark' : 'light')
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const fetchFeed = async () => {
    setLoading(true)
    setError(null)
    try {
      const tok = localStorage.getItem('token')
      if (!tok) throw new Error('Not authenticated')
      const res = await fetch('/feed?limit=10', {
        headers: { 'Authorization': `Bearer ${tok}` }
      })
      if (res.status === 401) {
        // force re-login UI
        localStorage.removeItem('token')
        setToken(null)
        setAuthError('Session expired. Please log in.')
        throw new Error('Not authenticated')
      }
      if (!res.ok) throw new Error('Failed to fetch feed')
      const data: FeedResponse = await res.json()
      setFeed(data.posts)
    } catch (e: any) {
      setError(e.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!token) return
    fetchFeed()
  }, [token])

  const doLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setAuthError(null)
    setLoggingIn(true)
    try {
      localStorage.setItem('username', username)
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      })
      if (!res.ok) throw new Error('Login failed')
      const data = await res.json()
      localStorage.setItem('token', data.token)
      setToken(data.token)
    } catch (err: any) {
      setAuthError(err.message || 'Login failed')
    } finally {
      setLoggingIn(false)
    }
  }

  useEffect(() => {
    const closeMenus = () => setOpenMenu(null)
    document.addEventListener('click', closeMenus)
    return () => document.removeEventListener('click', closeMenus)
  }, [])

  // Global ripple effect for any element with class "ripple"
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null
      if (!target) return
      const el = target.closest('.ripple') as HTMLElement | null
      if (!el) return

      const rect = el.getBoundingClientRect()
      const size = Math.max(rect.width, rect.height)
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2

      const ink = document.createElement('span')
      ink.className = 'r-ink'
      ink.style.width = ink.style.height = `${size}px`
      ink.style.left = `${x}px`
      ink.style.top = `${y}px`
      el.appendChild(ink)
      ink.addEventListener('animationend', () => ink.remove())
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [])

  const markSeen = async (post: Post) => {
    try {
      const token = localStorage.getItem('token')
      await fetch('/interactions/next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(post)
      })
    } catch {}
  }

  const onVote = async (post: Post, dir: 'up' | 'down', key: string) => {
    try {
      const url = dir === 'up' ? '/interactions/like' : '/interactions/dislike'
      const token = localStorage.getItem('token')
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(post)
      })
      // Also mark as seen for stats consistency
      markSeen(post)
      setVotes(prev => ({ ...prev, [key]: dir }))
    } catch {}
  }

  const onJudgeAI = async (post: Post, isAI: boolean) => {
    try {
      const token = localStorage.getItem('token')
      await fetch('/interactions/judgeAI', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ post, isAI })
      })
    } catch {}
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">slop</div>
        {token && (
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="pill subtle">{username}</span>
            <button className="ghost" onClick={() => { localStorage.removeItem('token'); setToken(null); setFeed([]); }}>Log out</button>
          </div>
        )}
      </header>

      {!token && (
        <main className="feed" style={{ maxWidth: 720, margin: '2rem auto' }}>
          <form onSubmit={doLogin} className="card" style={{ padding: '1rem' }}>
            <h2>Log in</h2>
            {authError && <div className="banner error" style={{ marginBottom: '0.5rem' }}>{authError}</div>}
            <label htmlFor="username">Username</label>
            <input id="username" value={username} onChange={e => setUsername(e.target.value)} placeholder="your name" />
            <div style={{ height: '0.5rem' }} />
            <button className="ripple" type="submit" disabled={loggingIn}>{loggingIn ? 'Logging in…' : 'Continue'}</button>
            <p className="muted" style={{ marginTop: '0.5rem' }}>No password needed in dev. A user will be created if it doesn’t exist.</p>
          </form>
        </main>
      )}

      {error && <div className="banner error">{error}</div>}

      {token && (
      <main className="feed">
        {feed.map((p, i) => {
          const key = `${p.post_id || i}-${i}`
          const voted = votes[key]
          return (
          <article className="post" key={key}>
            <button
              className="menu-btn ripple"
              aria-label="Post menu"
              onClick={(e) => {
                e.stopPropagation()
                setOpenMenu(openMenu === i ? null : i)
              }}
            />
            {openMenu === i && (
              <div className="menu" onClick={(e) => e.stopPropagation()}>
                <button className="ripple" onClick={() => { onJudgeAI(p, true); setOpenMenu(null) }}>Mark as AI generated</button>
              </div>
            )}
            <div className="vote-rail">
              <button aria-label="Upvote" onClick={() => onVote(p, 'up', key)} className={`icon up ripple ${voted === 'up' ? 'active' : ''}`} />
              <button aria-label="Downvote" onClick={() => onVote(p, 'down', key)} className={`icon down ripple ${voted === 'down' ? 'active' : ''}`} />
            </div>
            <div className="post-body">
              <h2 className="post-title">{p.title}</h2>
              <p className="post-text">{p.self_text}</p>
              <div className="post-meta">
                <span className="pill">r/{p.subreddit || 'ucla'}</span>
                {p.link_flair_text && !p.is_ai && p.link_flair_text !== 'AI' && (
                  <span className="pill subtle">{p.link_flair_text}</span>
                )}
                {p.is_ai && <span className="pill ai">AI</span>}
              </div>
              <div className="post-actions" />
            </div>
          </article>
        )})}
      </main>
      )}

      {token && (
        <footer className="pager">
          <button className="ghost" onClick={async () => { await fetchFeed(); window.scrollTo({ top: 0, behavior: 'smooth' }) }} disabled={loading}>
            {loading ? 'Loading…' : 'Next page →'}
          </button>
        </footer>
      )}
    </div>
  )
}


