# Learning Guide: tsvetkov.blog

Этот гайд описывает техническую реализацию блога через призму обучения. Если ты знаешь базовый HTML/CSS и начинаешь изучать JavaScript/React — этот проект отличный полигон для понимания, как всё работает вместе.

---

## Структура проекта

```
tsvetkov.blog/
├── index.html              # Главная страница
├── styles.css              # Все стили сайта
├── robots.txt              # Инструкции для поисковых роботов
├── sitemap.xml             # Карта сайта для поисковиков
├── favicon.ico             # Иконка вкладки браузера
├── CNAME                   # Конфигурация домена для GitHub Pages
├── posts/                  # Папка со страницами статей
│   ├── b2b-is-not-about-bigger-money.html
│   ├── memes-can-be-mirrors.html
│   └── memes-are-product-ideas.html
├── pics/                   # Папка с изображениями
│   ├── dna.jpeg
│   ├── Duolingo_meme.png
│   └── Yoda_meme.jpg
└── docs/                   # Документация
    └── Learning_guide.md   # Этот файл
```

**Ключевой момент:** Это статический сайт — просто HTML/CSS/JS файлы без серверной логики. GitHub Pages хостит их как есть.

---

## CSS: Что здесь можно изучить

### 1. CSS Custom Properties (переменные)

```css
/* Светлая тема (по умолчанию) */
:root {
    --color-bg: #ffffff;
    --color-text: #1a1a1a;
    --color-accent: #0a0a0a;
    --spacing-md: 1.5rem;
    --transition: 0.2s ease;
}

/* Тёмная тема (активируется через data-атрибут) */
[data-theme="dark"] {
    --color-bg: #0a0a0a;
    --color-text: #e8e8e8;
    --color-accent: #f5f5f5;
}
```

**Что это:** Переменные, объявленные в `:root`, доступны везде в CSS. Селектор `[data-theme="dark"]` переопределяет их когда на `<html>` есть атрибут `data-theme="dark"`.

**Как использовать:**
```css
body {
    background-color: var(--color-bg);
    color: var(--color-text);
}
```

**Зачем:**
- Меняешь цвет в одном месте — меняется везде
- Легко создать тёмную/светлую тему (просто переопределяешь переменные)
- Код становится читаемым: `var(--spacing-md)` понятнее чем `1.5rem`

**Связь с React:** В React ты будешь использовать CSS-in-JS (styled-components, emotion) или CSS Modules, но концепция переменных та же — один источник правды для значений.

---

### 2. Flexbox

```css
.blog-post-inner {
    display: flex;
    gap: var(--spacing-md);
}

.blog-post-thumbnail {
    flex-shrink: 0;      /* Не сжимать картинку */
    width: 120px;
}

.blog-post-content {
    flex: 1;             /* Занять всё оставшееся место */
    min-width: 0;        /* Разрешить сжатие текста */
}
```

**Что происходит:**
- `display: flex` — дети выстраиваются в ряд
- `gap` — отступ между детьми (современная альтернатива margin)
- `flex-shrink: 0` — элемент не будет сжиматься
- `flex: 1` — элемент займёт всё свободное пространство
- `min-width: 0` — хак для текста, чтобы он мог сжиматься (по умолчанию min-width: auto)

**Где ещё используется:**
```css
.search-container {
    display: flex;
    align-items: center;  /* Вертикальное центрирование */
    gap: var(--spacing-xs);
}
```

**Связь с React:** Flexbox используется абсолютно так же. В React-проектах часто используют Tailwind CSS, где это выглядит как `className="flex items-center gap-2"`.

---

### 3. Responsive Design (адаптивность)

```css
/* Базовые стили — для больших экранов */
.blog-post-thumbnail {
    width: 120px;
    height: 120px;
}

/* Переопределение для маленьких экранов */
@media (max-width: 640px) {
    .blog-post-thumbnail {
        width: 90px;
        height: 90px;
    }
}
```

**Логика:** Mobile-first или Desktop-first подход. Здесь Desktop-first: сначала стили для больших экранов, потом `@media` переопределяет для маленьких.

**Современный подход — `clamp()`:**
```css
.hero-name {
    font-size: clamp(2.5rem, 8vw, 4rem);
}
```
Это означает: минимум 2.5rem, максимум 4rem, а между ними — 8% от ширины viewport. Автоматическая адаптация без media queries.

**Связь с React:** Те же принципы. В React-проектах часто используют CSS-фреймворки (Tailwind, Chakra UI), которые дают готовые брейкпоинты.

---

### 4. CSS Animations

```css
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hero {
    animation: fadeIn 0.6s ease-out;
}

.about {
    animation: fadeIn 0.6s ease-out;
    animation-delay: 0.1s;          /* Начать позже */
    animation-fill-mode: both;       /* Сохранить состояние до/после */
}
```

**Что происходит:**
- `@keyframes` определяет анимацию (от состояния А к состоянию Б)
- `animation` применяет её к элементу
- `animation-delay` создаёт каскадный эффект (секции появляются по очереди)
- `animation-fill-mode: both` — элемент невидим до начала анимации и остаётся видимым после

**Связь с React:** В React для анимаций используют:
- CSS transitions/animations (как здесь)
- Framer Motion (декларативные анимации)
- React Spring (физически-корректные анимации)

---

### 5. Transitions (плавные переходы)

```css
.search-input {
    width: 0;
    opacity: 0;
    transition: all 0.3s ease;
}

.search-container.active .search-input {
    width: 200px;
    opacity: 1;
}
```

**Разница animation vs transition:**
- `animation` — запускается сама, можно зациклить
- `transition` — срабатывает при изменении свойства (hover, добавление класса)

**Здесь:** JavaScript добавляет класс `.active`, CSS плавно анимирует изменение ширины и прозрачности.

---

### 6. Переключение темы (Light/Dark Mode)

Это комплексная фича, которая объединяет CSS-переменные, JavaScript и localStorage.

**CSS — два набора переменных:**
```css
/* Светлая тема по умолчанию */
:root {
    --color-bg: #ffffff;
    --color-text: #1a1a1a;
}

/* Тёмная тема — переопределение */
[data-theme="dark"] {
    --color-bg: #0a0a0a;
    --color-text: #e8e8e8;
}
```

**CSS — плавный переход при смене темы:**
```css
html, body {
    transition: background-color 0.3s ease, color 0.3s ease;
}
```

**CSS — переключение иконок:**
```css
/* По умолчанию показываем луну (для перехода к тёмной) */
.theme-toggle .icon-sun {
    display: none;
}

/* В тёмной теме показываем солнце (для перехода к светлой) */
[data-theme="dark"] .theme-toggle .icon-sun {
    display: block;
}

[data-theme="dark"] .theme-toggle .icon-moon {
    display: none;
}
```

**UX-принцип:** Иконка показывает *куда* переключишься, а не *где* находишься. Это стандарт индустрии (GitHub, VS Code, Discord).

**JavaScript — переключение и сохранение:**
```javascript
const themeToggle = document.getElementById('themeToggle');

function setTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('theme', theme);
}

themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
});
```

**JavaScript — предотвращение мигания (FOUC):**
```html
<head>
    <script>
        // Выполняется ДО загрузки CSS
        (function() {
            const theme = localStorage.getItem('theme') || 'light';
            if (theme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            }
        })();
    </script>
    <!-- CSS загружается после -->
</head>
```

**Почему это важно:** Без этого скрипта пользователь увидит "вспышку" светлой темы перед переключением на тёмную. Скрипт в `<head>` выполняется синхронно до рендеринга страницы.

**localStorage:**
- `localStorage.setItem('theme', 'dark')` — сохранить
- `localStorage.getItem('theme')` — прочитать
- Данные сохраняются даже после закрытия браузера

**Связь с React:**
```jsx
const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
});

useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}, [theme]);

return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
        {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
    </button>
);
```

---

## JavaScript: Что здесь можно изучить

### 1. DOM Selection (выбор элементов)

```javascript
const searchToggle = document.getElementById('searchToggle');
const searchInput = document.getElementById('searchInput');
const searchContainer = document.querySelector('.search-container');
const blogPosts = document.querySelectorAll('.blog-post');
```

**Методы:**
- `getElementById('id')` — один элемент по ID
- `querySelector('.class')` — первый элемент по CSS-селектору
- `querySelectorAll('.class')` — все элементы (возвращает NodeList)

**Связь с React:** В React ты НЕ будешь напрямую работать с DOM. Вместо этого:
```jsx
// React использует refs для доступа к DOM (редко нужно)
const inputRef = useRef(null);

// Обычно ты просто описываешь UI декларативно
return <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
```

---

### 2. Event Listeners (обработчики событий)

```javascript
searchToggle.addEventListener('click', () => {
    searchContainer.classList.toggle('active');
    if (searchContainer.classList.contains('active')) {
        searchInput.focus();
    }
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        searchContainer.classList.remove('active');
        searchInput.value = '';
        filterPosts('');
    }
});

searchInput.addEventListener('input', (e) => {
    filterPosts(e.target.value);
});
```

**События:**
- `click` — клик мышью
- `keydown` — нажатие клавиши
- `input` — изменение значения в поле ввода

**Объект события (e):**
- `e.key` — какая клавиша нажата
- `e.target` — элемент, на котором сработало событие
- `e.target.value` — текущее значение input

**Связь с React:** В React события передаются как props:
```jsx
<button onClick={() => setActive(!active)}>Toggle</button>
<input
    onKeyDown={(e) => e.key === 'Escape' && setActive(false)}
    onChange={(e) => setSearchTerm(e.target.value)}
/>
```

---

### 3. DOM Manipulation (изменение DOM)

```javascript
// Добавить/убрать/переключить класс
searchContainer.classList.toggle('active');
searchContainer.classList.add('active');
searchContainer.classList.remove('active');
searchContainer.classList.contains('active'); // true/false

// Изменить значение input
searchInput.value = '';

// Показать/скрыть элемент
post.style.display = matches ? '' : 'none';

// Установить фокус
searchInput.focus();
```

**Связь с React:** В React ты не манипулируешь DOM напрямую. Вместо этого:
```jsx
const [isActive, setIsActive] = useState(false);

return (
    <div className={isActive ? 'search-container active' : 'search-container'}>
        {/* React сам обновит DOM когда isActive изменится */}
    </div>
);
```

---

### 4. Функции и логика фильтрации

```javascript
function filterPosts(query) {
    const searchTerm = query.toLowerCase().trim();

    blogPosts.forEach(post => {
        const title = post.querySelector('h3').textContent.toLowerCase();
        const preview = post.querySelector('.blog-post-content p').textContent.toLowerCase();
        const matches = searchTerm === '' ||
                        title.includes(searchTerm) ||
                        preview.includes(searchTerm);

        post.style.display = matches ? '' : 'none';
    });
}
```

**Разбор:**
- `query.toLowerCase()` — привести к нижнему регистру (поиск регистронезависимый)
- `.trim()` — убрать пробелы по краям
- `blogPosts.forEach()` — перебрать все посты
- `.textContent` — получить текст элемента
- `.includes()` — проверить, содержит ли строка подстроку
- Тернарный оператор: `condition ? valueIfTrue : valueIfFalse`

**Связь с React:** Логика фильтрации будет похожей, но данные хранятся в state:
```jsx
const [posts, setPosts] = useState([...]);
const [searchTerm, setSearchTerm] = useState('');

const filteredPosts = posts.filter(post =>
    post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    post.preview.toLowerCase().includes(searchTerm.toLowerCase())
);

return filteredPosts.map(post => <PostCard key={post.id} {...post} />);
```

---

## SEO: Что здесь можно изучить

### 1. Meta теги

```html
<meta name="description" content="Описание страницы для поисковиков">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**description** — показывается в результатах поиска Google под заголовком.

**viewport** — критически важен для мобильных. Без него сайт будет отображаться как десктопная версия, уменьшенная до размера экрана.

---

### 2. Open Graph (для соцсетей)

```html
<meta property="og:type" content="article">
<meta property="og:title" content="Заголовок">
<meta property="og:description" content="Описание">
<meta property="og:image" content="https://tsvetkov.blog/pics/image.jpg">
<meta property="og:url" content="https://tsvetkov.blog/posts/post.html">
```

**Что это:** Когда кто-то делится ссылкой в Telegram, Twitter, LinkedIn — эти теги определяют, как будет выглядеть превью (картинка, заголовок, описание).

**og:type:**
- `website` — для главной страницы
- `article` — для статей/постов

---

### 3. JSON-LD (структурированные данные)

```html
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "Заголовок статьи",
    "datePublished": "2026-01-24",
    "author": {
        "@type": "Person",
        "name": "Evgeniy Tsvetkov"
    }
}
</script>
```

**Что это:** Машиночитаемая разметка для Google. Позволяет показывать расширенные сниппеты в поиске (с датой, автором, рейтингом и т.д.).

**Связь с React:** В React (особенно Next.js) есть специальные компоненты для SEO:
```jsx
import Head from 'next/head';

export default function Post({ post }) {
    return (
        <Head>
            <title>{post.title}</title>
            <meta property="og:title" content={post.title} />
            <script type="application/ld+json">
                {JSON.stringify({
                    "@context": "https://schema.org",
                    "@type": "BlogPosting",
                    "headline": post.title
                })}
            </script>
        </Head>
    );
}
```

---

### 4. robots.txt

```
User-agent: *
Allow: /
Sitemap: https://tsvetkov.blog/sitemap.xml
```

**Что это:** Инструкции для поисковых роботов.
- `User-agent: *` — для всех роботов
- `Allow: /` — разрешить индексировать всё
- `Sitemap:` — где искать карту сайта

**Можно запретить:**
```
Disallow: /admin/
Disallow: /private/
```

---

### 5. sitemap.xml

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://tsvetkov.blog/</loc>
        <lastmod>2026-01-24</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>
```

**Что это:** Список всех страниц сайта для поисковиков.
- `loc` — URL страницы
- `lastmod` — дата последнего изменения
- `changefreq` — как часто меняется (подсказка для робота)
- `priority` — важность страницы (0.0–1.0)

**Важно:** При добавлении нового поста нужно вручную добавить его в sitemap.

---

## Accessibility (доступность)

Accessibility (a11y) — это практики, которые делают сайт доступным для людей с ограниченными возможностями (например, использующих screen readers).

### aria-label

```html
<input type="text" placeholder="Search posts..." aria-label="Search posts">
<button aria-label="Toggle theme">
    <svg>...</svg>
</button>
```

**Зачем:** Screen reader не видит placeholder и не понимает, что внутри SVG. `aria-label` даёт текстовое описание элемента.

**Когда использовать:**
- Input без видимого `<label>`
- Кнопки с иконками без текста
- Интерактивные элементы, чей смысл неочевиден из контекста

### Семантические теги

```html
<header class="hero">...</header>
<article class="blog-post">...</article>
<footer class="footer">...</footer>
<time datetime="2026-01-24">January 24, 2026</time>
```

**Зачем:** Screen readers и поисковики понимают структуру страницы. `<article>` — это самостоятельный контент, `<time>` — машиночитаемая дата.

**Связь с React:** Те же принципы. В React часто забывают про семантику, используя `<div>` везде. Не делай так.

---

## Как это всё связано с React

| Vanilla JS (этот проект) | React |
|--------------------------|-------|
| `document.getElementById()` | `useRef()` (редко нужно) |
| `element.addEventListener()` | `onClick`, `onChange` props |
| `element.classList.toggle()` | `useState()` + условный className |
| `element.style.display = 'none'` | Условный рендеринг `{show && <Component />}` |
| `element.innerHTML = '...'` | JSX: `return <div>...</div>` |
| Ручное обновление DOM | React сам обновляет DOM при изменении state |

**Главное отличие:**
- **Vanilla JS:** Ты говоришь браузеру ЧТО ДЕЛАТЬ (императивный подход)
- **React:** Ты описываешь КАК ДОЛЖНО ВЫГЛЯДЕТЬ при данном состоянии (декларативный подход)

```javascript
// Vanilla JS — императивно
if (isActive) {
    element.classList.add('active');
} else {
    element.classList.remove('active');
}
```

```jsx
// React — декларативно
<div className={isActive ? 'active' : ''} />
// React сам разберётся, что добавить/убрать в DOM
```

---

## Практические задания

Если хочешь закрепить знания на этом проекте:

### Уровень 1 (CSS)
1. Добавь hover-эффект на карточки постов (например, лёгкое поднятие)
2. Сделай плавное появление результатов поиска
3. Добавь третью тему (например, "sepia" для чтения) с переключателем

### Уровень 2 (JavaScript)
1. Добавь подсветку найденного текста в результатах поиска
2. Сделай счётчик найденных постов ("Found 2 of 3 posts")
3. Добавь debounce для поиска (не фильтровать на каждый символ)

### Уровень 3 (Переписать на React)
1. Создай React-версию блога с теми же функциями
2. Вынеси данные постов в JSON и загружай их
3. Добавь роутинг (React Router) для страниц постов

---

## Полезные ресурсы

- [CSS Tricks — Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [MDN — JavaScript Events](https://developer.mozilla.org/en-US/docs/Web/Events)
- [React — Official Tutorial](https://react.dev/learn)
- [Schema.org — Structured Data](https://schema.org/BlogPosting)
