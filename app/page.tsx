'use client'

import { useState } from 'react'
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

  return (
    <main>
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
              <a href="#order" className="btn btn-primary">Замовити відео</a>
              <a href="#portfolio" className="btn btn-secondary">Переглянути роботи</a>
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
              <div className="service-icon">📸</div>
              <h3>Індивідуальний підхід</h3>
              <p>Кожне відео створюється індивідуально під ваші фотографії та побажання</p>
            </div>
            <div className="service-card">
              <div className="service-icon">🎵</div>
              <h3>Вибір музики</h3>
              <p>Ви обираєте музику, яка найкраще передає атмосферу вашої події</p>
            </div>
            <div className="service-card">
              <div className="service-icon">✨</div>
              <h3>Професійні ефекти</h3>
              <p>Сучасні AI-ефекти та анімації для створення незабутнього відео</p>
            </div>
            <div className="service-card">
              <div className="service-icon">🎬</div>
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
                <li>Вартість залежить від тривалості</li>
                <li>Вибір ефектів та стилю</li>
                <li>Ваша музика</li>
                <li>Готове відео високої якості</li>
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
                <li>Знижка на кожне відео</li>
                <li>Пріоритетна обробка</li>
                <li>Додаткові ефекти безкоштовно</li>
                <li>Індивідуальний підхід</li>
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
              <div className="portfolio-placeholder">
                <div className="play-icon">▶</div>
                <p>Приклад відео</p>
              </div>
            </div>
            <div className="portfolio-item">
              <div className="portfolio-placeholder">
                <div className="play-icon">▶</div>
                <p>Приклад відео</p>
              </div>
            </div>
            <div className="portfolio-item">
              <div className="portfolio-placeholder">
                <div className="play-icon">▶</div>
                <p>Приклад відео</p>
              </div>
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
            </button>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>&copy; 2026 AI Відео з Фотографій. Всі права захищені.</p>
        </div>
      </footer>
    </main>
  )
}
