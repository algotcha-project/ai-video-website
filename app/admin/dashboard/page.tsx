'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut, Plus, Trash2, Video } from 'lucide-react'
import '../admin.css'

interface Video {
  id: string
  title: string
  description: string
  url: string
  type: string
}

export default function AdminDashboard() {
  const [videos, setVideos] = useState<Video[]>([])
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    url: '',
    type: 'wedding'
  })
  const router = useRouter()

  useEffect(() => {
    // Check authentication
    const auth = sessionStorage.getItem('adminAuth')
    if (!auth) {
      router.push('/admin')
      return
    }

    // Load videos from localStorage
    const storedVideos = localStorage.getItem('adminVideos')
    if (storedVideos) {
      setVideos(JSON.parse(storedVideos))
    }
  }, [router])

  const handleLogout = () => {
    sessionStorage.removeItem('adminAuth')
    router.push('/admin')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const newVideo: Video = {
      id: Date.now().toString(),
      title: formData.title,
      description: formData.description,
      url: formData.url,
      type: formData.type
    }

    const updatedVideos = [...videos, newVideo]
    setVideos(updatedVideos)
    localStorage.setItem('adminVideos', JSON.stringify(updatedVideos))

    // Reset form
    setFormData({
      title: '',
      description: '',
      url: '',
      type: 'wedding'
    })
  }

  const handleDelete = (id: string) => {
    if (confirm('Ви впевнені, що хочете видалити це відео?')) {
      const updatedVideos = videos.filter(video => video.id !== id)
      setVideos(updatedVideos)
      localStorage.setItem('adminVideos', JSON.stringify(updatedVideos))
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-container">
        <div className="admin-dashboard-header">
          <h1>Панель управління</h1>
          <button onClick={handleLogout} className="admin-logout-btn">
            <LogOut size={18} />
            Вийти
          </button>
        </div>

        <div className="admin-section">
          <h2>
            <Plus size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />
            Додати нове відео
          </h2>
          <form onSubmit={handleSubmit} className="admin-video-form">
            <div className="admin-form-row">
              <div className="admin-form-group">
                <label htmlFor="title">Назва відео *</label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  required
                  placeholder="Наприклад: Весілля Оксани та Івана"
                />
              </div>
              <div className="admin-form-group">
                <label htmlFor="type">Тип події *</label>
                <select
                  id="type"
                  name="type"
                  value={formData.type}
                  onChange={handleChange}
                  required
                >
                  <option value="wedding">Весілля</option>
                  <option value="birthday">День народження</option>
                  <option value="anniversary">Ювілей</option>
                  <option value="corporate">Корпоратив</option>
                  <option value="other">Інше</option>
                </select>
              </div>
            </div>
            <div className="admin-form-group">
              <label htmlFor="url">URL відео (YouTube, Vimeo або інше) *</label>
              <input
                type="url"
                id="url"
                name="url"
                value={formData.url}
                onChange={handleChange}
                required
                placeholder="https://www.youtube.com/watch?v=..."
              />
            </div>
            <div className="admin-form-group">
              <label htmlFor="description">Опис</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Короткий опис відео..."
              />
            </div>
            <button type="submit" className="admin-submit-btn">
              <Plus size={18} />
              Додати відео
            </button>
          </form>
        </div>

        <div className="admin-section">
          <h2>
            <Video size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />
            Додані відео ({videos.length})
          </h2>
          {videos.length === 0 ? (
            <p style={{ color: 'var(--gray)', textAlign: 'center', padding: '40px' }}>
              Поки що немає доданих відео
            </p>
          ) : (
            <div className="admin-videos-list">
              {videos.map((video) => (
                <div key={video.id} className="admin-video-card">
                  <h3>{video.title}</h3>
                  <p>
                    <strong>Тип:</strong> {
                      video.type === 'wedding' ? 'Весілля' :
                      video.type === 'birthday' ? 'День народження' :
                      video.type === 'anniversary' ? 'Ювілей' :
                      video.type === 'corporate' ? 'Корпоратив' : 'Інше'
                    }
                  </p>
                  {video.description && <p>{video.description}</p>}
                  <a href={video.url} target="_blank" rel="noopener noreferrer">
                    {video.url}
                  </a>
                  <button
                    onClick={() => handleDelete(video.id)}
                    className="admin-delete-btn"
                  >
                    <Trash2 size={16} style={{ display: 'inline-block', marginRight: '4px', verticalAlign: 'middle' }} />
                    Видалити
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
