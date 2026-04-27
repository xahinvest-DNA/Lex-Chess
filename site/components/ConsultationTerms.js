export default function ConsultationTerms() {
  return (
    <section className="terms-panel" aria-labelledby="consultation-terms">
      <div>
        <p className="eyebrow">Условия консультации</p>
        <h2 id="consultation-terms">Сначала оценка ситуации, затем согласование формата и объема работы.</h2>
        <p>
          На сайте используется безопасная и юридически корректная подача: стоимость, длительность и формат
          консультации уточняются после первичной диагностики. Это позволяет не обещать лишнего до анализа документов и
          фактов.
        </p>
      </div>
      <div className="terms-grid">
        <article>
          <strong>Формат</strong>
          <span>Телефон, Telegram, онлайн-встреча или очная консультация по согласованию.</span>
        </article>
        <article>
          <strong>Длительность</strong>
          <span>Ориентир по времени обсуждается после первичной оценки ситуации и срочности вопроса.</span>
        </article>
        <article>
          <strong>Стоимость</strong>
          <span>Уточняется до консультации. Если услуга платная, условия согласуются заранее.</span>
        </article>
        <article>
          <strong>Результат</strong>
          <span>Юрист помогает определить маршрут, риски, документы и следующий шаг без гарантий исхода дела.</span>
        </article>
      </div>
    </section>
  );
}
