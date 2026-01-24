'use client'

import { useState } from 'react'
import { Camera, Music, Sparkles, Film, Play, Check, ArrowRight, Mail, Phone, User, Calendar, Video, MessageCircle, X, Send, Sparkle as SparkleIcon, Star, Award, Clock, Zap } from 'lucide-react'
import './page.css'

export default function Home() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    occasion: '',
    videoCount: '1',
    message: ''
  })
  
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessage, setChatMessage] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Here you would typically send the form data to your backend
    alert('Дякуємо за заявку! Ми зв\'яжемося з вами найближчим часом.')
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
                <div className="chat-avatar">O</div>
                <div>
                  <h4>Олег</h4>
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
        <div className="hero-background">
          <div className="gradient-overlay"></div>
        </div>
        <div className="container">
          <div className="hero-content">
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
            <div className="portfolio-item">
              <div className="video-container">
                <div className="video-placeholder">
                  <div className="video-pattern"></div>
                  <div className="video-content">
                    <div className="play-button-large">
                      <Play size={48} fill="currentColor" />
                    </div>
                    <h4>Весілля</h4>
                    <p>Романтичне відео з весільної церемонії</p>
                  </div>
                </div>
                <div className="video-overlay">
                  <div className="video-label">Весілля</div>
                </div>
              </div>
            </div>
            <div className="portfolio-item">
              <div className="video-container">
                <div className="video-placeholder">
                  <div className="video-pattern"></div>
                  <div className="video-content">
                    <div className="play-button-large">
                      <Play size={48} fill="currentColor" />
                    </div>
                    <h4>День народження</h4>
                    <p>Веселе відео з дня народження</p>
                  </div>
                </div>
                <div className="video-overlay">
                  <div className="video-label">День народження</div>
                </div>
              </div>
            </div>
            <div className="portfolio-item">
              <div className="video-container">
                <div className="video-placeholder">
                  <div className="video-pattern"></div>
                  <div className="video-content">
                    <div className="play-button-large">
                      <Play size={48} fill="currentColor" />
                    </div>
                    <h4>Ювілей</h4>
                    <p>Торжественне відео до ювілею</p>
                  </div>
                </div>
                <div className="video-overlay">
                  <div className="video-label">Ювілей</div>
                </div>
              </div>
            </div>
          </div>
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
            <button type="submit" className="btn btn-primary form-submit">
              Відправити заявку
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
              <a href="https://t.me/oleg030696" target="_blank" rel="noopener noreferrer" className="footer-link">
                <MessageCircle size={18} />
                Telegram: @oleg030696
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
