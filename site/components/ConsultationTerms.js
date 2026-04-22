export default function ConsultationTerms() {
  return (
    <section className="terms-panel" aria-labelledby="consultation-terms">
      <div>
        <p className="eyebrow">Условия консультации</p>
        <h2 id="consultation-terms">Первичная диагностика без обещаний результата.</h2>
        <p>
          Пока реальные коммерческие условия не утверждены, на сайте используется безопасная
          формулировка: стоимость, длительность и формат консультации согласуются после первичной
          диагностики и зависят от направления, срочности и объема документов.
        </p>
      </div>
      <div className="terms-grid">
        <article>
          <strong>Формат</strong>
          <span>Телефон, Telegram, онлайн-встреча или очная консультация по согласованию.</span>
        </article>
        <article>
          <strong>Длительность</strong>
          <span>Ориентир: 30-60 минут после предварительного изучения ситуации.</span>
        </article>
        <article>
          <strong>Стоимость</strong>
          <span>Определяется после диагностики. Если консультация платная, цена сообщается заранее.</span>
        </article>
        <article>
          <strong>Результат</strong>
          <span>Юрист дает правовую оценку и возможный маршрут, но не гарантирует исход дела.</span>
        </article>
      </div>
    </section>
  );
}
