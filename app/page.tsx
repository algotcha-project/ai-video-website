'use client'

import { useState, useEffect, useRef } from 'react'
import { Camera, Music, Sparkles, Film, Play, Check, ArrowRight, Mail, Phone, User, Calendar, Video, MessageCircle, X, Send, Sparkle as SparkleIcon, Star, Award, Clock, Zap, CheckCircle, AlertCircle } from 'lucide-react'
import './page.css'

interface Video {
  id: string
  title: string
  description: string
  url: string
  type: string
}

export default function Home() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    occasion: '',
    videoCount: '1',
    message: ''
  })
  
  const [submitStatus, setSubmitStatus] = useState<{
    type: 'success' | 'error' | null
    message: string
  }>({ type: null, message: '' })
  
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [adminVideos, setAdminVideos] = useState<Video[]>([])
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Array<{x: number, y: number, vx: number, vy: number, size: number}>>([])

  useEffect(() => {
    // Load videos from localStorage
    const storedVideos = localStorage.getItem('adminVideos')
    if (storedVideos) {
      setAdminVideos(JSON.parse(storedVideos))
    }
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Initialize particles
    const particleCount = 50
    particlesRef.current = Array.from({ length: particleCount }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1
    }))

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // Update and draw particles
      particlesRef.current.forEach(particle => {
        particle.x += particle.vx
        particle.y += particle.vy

        if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1
        if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1

        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(99, 102, 241, 0.1)'
        ctx.fill()
      })

      // Draw connections
      particlesRef.current.forEach((particle, i) => {
        particlesRef.current.slice(i + 1).forEach(otherParticle => {
          const dx = particle.x - otherParticle.x
          const dy = particle.y - otherParticle.y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance < 150) {
            ctx.beginPath()
            ctx.moveTo(particle.x, particle.y)
            ctx.lineTo(otherParticle.x, otherParticle.y)
            ctx.strokeStyle = `rgba(99, 102, 241, ${0.2 * (1 - distance / 150)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        })
      })

      requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Format occasion label
    const occasionLabels: Record<string, string> = {
      wedding: 'Весілля',
      birthday: 'День народження',
      anniversary: 'Ювілей',
      corporate: 'Корпоратив',
      other: 'Інше'
    }
    
    const occasionLabel = occasionLabels[formData.occasion] || formData.occasion
    
    // Build the message for Telegram
    const message = `🎬 НОВА ЗАЯВКА НА ВІДЕО

👤 Ім'я: ${formData.name}
📱 Телефон: ${formData.phone}
${formData.email ? `📧 Email: ${formData.email}` : ''}

📅 Тип події: ${occasionLabel}
🎥 Кількість відео: ${formData.videoCount}

${formData.message ? `💬 Додаткова інформація:\n${formData.message}` : ''}`

    // Open Telegram with the pre-filled message
    const telegramUrl = `https://t.me/oleg030696?text=${encodeURIComponent(message.trim())}`
    window.open(telegramUrl, '_blank')
    
    // Show success message and reset form
    setSubmitStatus({
      type: 'success',
      message: 'Telegram відкрито! Надішліть повідомлення, щоб завершити замовлення. 🎉'
    })
    setFormData({
      name: '',
      email: '',
      phone: '',
      occasion: '',
      videoCount: '1',
      message: ''
    })
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (chatMessage.trim()) {
      const telegramUrl = `https://t.me/oleg030696?text=${encodeURIComponent(chatMessage)}`
      window.open(telegramUrl, '_blank')
      setChatMessage('')
      setChatOpen(false)
    }
  }

  return (
    <main>
      {/* Floating Chat Widget */}
      <div className={`chat-widget ${chatOpen ? 'chat-open' : ''}`}>
        {chatOpen ? (
          <div className="chat-container">
            <div className="chat-header">
              <div className="chat-header-info">
                <div className="chat-telegram-logo">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161l-1.84 8.678c-.135.608-.479.758-.97.473l-2.677-1.97-1.29 1.24c-.146.146-.269.269-.552.269l.197-2.78 4.942-4.466c.216-.191-.047-.297-.335-.105l-6.105 3.846-2.637-.823c-.574-.179-.589-.574.12-.87l10.32-3.977c.478-.18.896.112.74.694z"/>
                  </svg>
                </div>
                <div>
                  <h4>Telegram</h4>
                  <p>Онлайн</p>
                </div>
              </div>
              <button className="chat-close" onClick={() => setChatOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="chat-messages">
              <div className="chat-message bot">
                <p>Привіт! Я готовий відповісти на ваші питання про створення AI-відео. Напишіть мені в Telegram!</p>
              </div>
            </div>
            <form onSubmit={handleChatSubmit} className="chat-input-form">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Напишіть повідомлення..."
                className="chat-input"
              />
              <button type="submit" className="chat-send">
                <Send size={18} />
              </button>
            </form>
            <div className="chat-telegram-link">
              <a href="https://t.me/oleg030696" target="_blank" rel="noopener noreferrer" className="btn-telegram">
                <MessageCircle size={18} />
                Відкрити Telegram
              </a>
            </div>
          </div>
        ) : (
          <button className="chat-toggle" onClick={() => setChatOpen(true)}>
            <MessageCircle size={24} />
            <span className="chat-badge">1</span>
          </button>
        )}
      </div>
      {/* Hero Section */}
      <section className="hero">
        <canvas ref={canvasRef} className="particles-canvas"></canvas>
        <div className="hero-background">
          <div className="gradient-overlay"></div>
          <div className="floating-shapes">
            <div className="shape shape-1"></div>
            <div className="shape shape-2"></div>
            <div className="shape shape-3"></div>
            <div className="shape shape-4"></div>
          </div>
        </div>
        <div className="container">
          <div className="hero-content">
            <div className="logo-container">
              <div className="logo">
                <Video size={48} />
                <Sparkles size={32} className="logo-sparkle" />
              </div>
              <h2 className="site-name">MemoriaAI</h2>
            </div>
            <h1 className="hero-title">
              Створюємо унікальні <span className="highlight">AI-відео</span> з ваших фотографій
            </h1>
            <p className="hero-subtitle">
              Професійні відео на замовлення для будь-якої події: весілля, дні народження, ювілеї та інші особливі моменти життя
            </p>
            <div className="hero-buttons">
              <a href="#order" className="btn btn-primary">
                Замовити відео
                <ArrowRight size={20} style={{ marginLeft: '8px', display: 'inline-block' }} />
              </a>
              <a href="#portfolio" className="btn btn-secondary">Переглянути роботи</a>
            </div>
            <div className="hero-contact">
              <a href="tel:+380968753003" className="hero-phone">
                <Phone size={18} />
                +380 96 875 3003
              </a>
            </div>
            <div className="hero-stats-preview">
              <div className="stat-preview">
                <span className="stat-preview-number">500+</span>
                <span className="stat-preview-label">відео</span>
              </div>
              <div className="stat-preview">
                <span className="stat-preview-number">98%</span>
                <span className="stat-preview-label">задоволених</span>
              </div>
              <div className="stat-preview">
                <span className="stat-preview-number">24-48</span>
                <span className="stat-preview-label">годин</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="section stats">
        <div className="container">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">
                <Video size={32} />
              </div>
              <div className="stat-number">500+</div>
              <div className="stat-label">Створених відео</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <Star size={32} />
              </div>
              <div className="stat-number">98%</div>
              <div className="stat-label">Задоволених клієнтів</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <Clock size={32} />
              </div>
              <div className="stat-number">24-48</div>
              <div className="stat-label">Годин на виконання</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <Award size={32} />
              </div>
              <div className="stat-number">5+</div>
              <div className="stat-label">Років досвіду</div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="section services">
        <div className="container">
          <h2 className="section-title">Наші послуги</h2>
          <p className="section-subtitle">
            Ми перетворюємо ваші найкращі спогади в динамічні відео з музикою та професійними ефектами
          </p>
          <div className="services-grid">
            <div className="service-card">
              <div className="service-icon-wrapper">
                <Camera className="service-icon" size={48} strokeWidth={1.5} />
              </div>
              <h3>Індивідуальний підхід</h3>
              <p>Кожне відео створюється індивідуально під ваші фотографії та побажання</p>
            </div>
            <div className="service-card">
              <div className="service-icon-wrapper">
                <Music className="service-icon" size={48} strokeWidth={1.5} />
              </div>
              <h3>Вибір музики</h3>
              <p>Ви обираєте музику, яка найкраще передає атмосферу вашої події</p>
            </div>
            <div className="service-card">
              <div className="service-icon-wrapper">
                <Sparkles className="service-icon" size={48} strokeWidth={1.5} />
              </div>
              <h3>Професійні ефекти</h3>
              <p>Сучасні AI-ефекти та анімації для створення незабутнього відео</p>
            </div>
            <div className="service-card">
              <div className="service-icon-wrapper">
                <Film className="service-icon" size={48} strokeWidth={1.5} />
              </div>
              <h3>Будь-яка подія</h3>
              <p>Весілля, дні народження, ювілеї, корпоративи та інші особливі моменти</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="section pricing" id="pricing">
        <div className="container">
          <h2 className="section-title">Вартість послуг</h2>
          <p className="section-subtitle">
            Прозорі ціни та вигідні умови при замовленні кількох відео
          </p>
          <div className="pricing-grid">
            <div className="pricing-card">
              <div className="pricing-header">
                <h3>Одне відео</h3>
                <div className="price">
                  <span className="price-amount">500-750</span>
                  <span className="price-currency">₴</span>
                </div>
              </div>
              <ul className="pricing-features">
                <li><Check size={18} /> Вартість залежить від тривалості</li>
                <li><Check size={18} /> Вибір ефектів та стилю</li>
                <li><Check size={18} /> Ваша музика</li>
                <li><Check size={18} /> Готове відео високої якості</li>
              </ul>
            </div>
            <div className="pricing-card featured">
              <div className="pricing-badge">Вигідно</div>
              <div className="pricing-header">
                <h3>Пакет 3+ відео</h3>
                <div className="price">
                  <span className="price-amount">Знижка</span>
                </div>
              </div>
              <ul className="pricing-features">
                <li><Check size={18} /> Знижка на кожне відео</li>
                <li><Check size={18} /> Пріоритетна обробка</li>
                <li><Check size={18} /> Додаткові ефекти безкоштовно</li>
                <li><Check size={18} /> Індивідуальний підхід</li>
              </ul>
            </div>
          </div>
          <p className="pricing-note">
            * Точна вартість залежить від тривалості відео та обраних ефектів. Деталі обговорюються індивідуально.
          </p>
        </div>
      </section>

      {/* Portfolio Section */}
      <section className="section portfolio" id="portfolio">
        <div className="container">
          <h2 className="section-title">Приклади робіт</h2>
          <p className="section-subtitle">
            Подивіться на приклади наших відео, створених для різних подій
          </p>
          <div className="portfolio-grid">
            {adminVideos.length > 0 ? (
              adminVideos.map((video) => {
                // Extract video ID from YouTube URL
                const getVideoId = (url: string) => {
                  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
                  const match = url.match(regExp)
                  return (match && match[2].length === 11) ? match[2] : null
                }

                const videoId = getVideoId(video.url)
                const embedUrl = videoId 
                  ? `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1&controls=1`
                  : video.url

                return (
                  <div key={video.id} className="portfolio-item">
                    <div className="video-container">
                      {videoId ? (
                        <iframe
                          src={embedUrl}
                          title={video.title}
                          frameBorder="0"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                          className="portfolio-video"
                        ></iframe>
                      ) : (
                        <div className="video-placeholder-card">
                          <div className="video-placeholder-icon">
                            <Video size={64} />
                          </div>
                          <h3>{video.title}</h3>
                          <p>{video.description || 'Відео'}</p>
                          <a href={video.url} target="_blank" rel="noopener noreferrer" className="video-placeholder-badge" style={{ textDecoration: 'none', display: 'inline-block', marginTop: '12px' }}>
                            Переглянути відео
                          </a>
                        </div>
                      )}
                      <div className="video-overlay">
                        <div className="video-label">{video.title}</div>
                      </div>
                    </div>
                  </div>
                )
              })
            ) : (
              <>
                <div className="portfolio-item">
                  <div className="video-placeholder-card">
                    <div className="video-placeholder-icon">
                      <Video size={64} />
                    </div>
                    <h3>Весілля</h3>
                    <p>Романтичне відео з весільної церемонії</p>
                    <div className="video-placeholder-badge">Приклад роботи</div>
                  </div>
                </div>
                <div className="portfolio-item">
                  <div className="video-placeholder-card">
                    <div className="video-placeholder-icon">
                      <Video size={64} />
                    </div>
                    <h3>День народження</h3>
                    <p>Веселе відео з дня народження</p>
                    <div className="video-placeholder-badge">Приклад роботи</div>
                  </div>
                </div>
                <div className="portfolio-item">
                  <div className="video-placeholder-card">
                    <div className="video-placeholder-icon">
                      <Video size={64} />
                    </div>
                    <h3>Ювілей</h3>
                    <p>Торжественне відео до ювілею</p>
                    <div className="video-placeholder-badge">Приклад роботи</div>
                  </div>
                </div>
              </>
            )}
          </div>
          {adminVideos.length === 0 && (
            <div className="portfolio-note">
              <p>Для перегляду реальних прикладів наших робіт, будь ласка, зв'яжіться з нами через Telegram</p>
            </div>
          )}
        </div>
      </section>

      {/* Process Section */}
      <section className="section process">
        <div className="container">
          <h2 className="section-title">Як ми працюємо</h2>
          <p className="section-subtitle">
            Простий процес створення вашого унікального відео
          </p>
          <div className="process-steps">
            <div className="process-step">
              <div className="process-number">1</div>
              <div className="process-icon">
                <Mail size={32} />
              </div>
              <h3>Залиште заявку</h3>
              <p>Заповніть форму або напишіть нам в Telegram</p>
            </div>
            <div className="process-arrow">
              <ArrowRight size={32} />
            </div>
            <div className="process-step">
              <div className="process-number">2</div>
              <div className="process-icon">
                <Camera size={32} />
              </div>
              <h3>Надішліть фотографії</h3>
              <p>Відправте ваші найкращі фото та оберіть музику</p>
            </div>
            <div className="process-arrow">
              <ArrowRight size={32} />
            </div>
            <div className="process-step">
              <div className="process-number">3</div>
              <div className="process-icon">
                <Sparkles size={32} />
              </div>
              <h3>Ми створюємо</h3>
              <p>Додаємо ефекти, анімації та обробляємо відео</p>
            </div>
            <div className="process-arrow">
              <ArrowRight size={32} />
            </div>
            <div className="process-step">
              <div className="process-number">4</div>
              <div className="process-icon">
                <Zap size={32} />
              </div>
              <h3>Отримайте результат</h3>
              <p>Готове відео високої якості за 24-48 годин</p>
            </div>
          </div>
        </div>
      </section>

      {/* Order Form Section */}
      <section className="section order-form" id="order">
        <div className="container">
          <h2 className="section-title">Замовити відео</h2>
          <p className="section-subtitle">
            Заповніть форму, і ми зв'яжемося з вами для обговорення деталей
          </p>
          <form onSubmit={handleSubmit} className="form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Ваше ім'я *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Введіть ваше ім'я"
                />
              </div>
              <div className="form-group">
                <label htmlFor="phone">Телефон *</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  required
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="+380 XX XXX XX XX"
                />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="occasion">Тип події *</label>
                <select
                  id="occasion"
                  name="occasion"
                  required
                  value={formData.occasion}
                  onChange={handleChange}
                >
                  <option value="">Оберіть тип події</option>
                  <option value="wedding">Весілля</option>
                  <option value="birthday">День народження</option>
                  <option value="anniversary">Ювілей</option>
                  <option value="corporate">Корпоратив</option>
                  <option value="other">Інше</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="videoCount">Кількість відео *</label>
                <select
                  id="videoCount"
                  name="videoCount"
                  required
                  value={formData.videoCount}
                  onChange={handleChange}
                >
                  <option value="1">1 відео</option>
                  <option value="2">2 відео</option>
                  <option value="3">3 відео</option>
                  <option value="4+">4+ відео</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="message">Додаткова інформація</label>
              <textarea
                id="message"
                name="message"
                rows={5}
                value={formData.message}
                onChange={handleChange}
                placeholder="Опишіть вашу подію, побажання щодо стилю, музики або інші деталі..."
              />
            </div>
            {submitStatus.type && (
              <div className={`form-status ${submitStatus.type}`}>
                {submitStatus.type === 'success' ? (
                  <CheckCircle size={20} />
                ) : (
                  <AlertCircle size={20} />
                )}
                <span>{submitStatus.message}</span>
              </div>
            )}
            <button 
              type="submit" 
              className="btn btn-primary form-submit"
            >
              Відправити в Telegram
              <ArrowRight size={20} style={{ marginLeft: '8px', display: 'inline-block' }} />
            </button>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h3>AI Відео з Фотографій</h3>
              <p>Створюємо унікальні відео з ваших спогадів</p>
            </div>
            <div className="footer-section">
              <h4>Контакти</h4>
              <a href="tel:+380968753003" className="footer-link">
                <Phone size={18} />
                +380 96 875 3003
              </a>
              <a href="https://t.me/oleg030696" target="_blank" rel="noopener noreferrer" className="footer-link">
                <MessageCircle size={18} />
                Telegram
              </a>
            </div>
            <div className="footer-section">
              <h4>Послуги</h4>
              <p>AI-відео для весіль</p>
              <p>Відео для днів народження</p>
              <p>Ювілейні відео</p>
              <p>Корпоративні відео</p>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2026 AI Відео з Фотографій. Всі права захищені.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
