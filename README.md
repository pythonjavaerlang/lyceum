# Чернівецький ліцей — статичний сайт (GitHub Pages, htmx)

Статичний сайт Чернівецького ліцею іноземних мов, комп’ютерних наук та
інформаційних технологій (`lyceum.cpbi.info`). Згенерований зі статичних
HTML-сторінок, з навігацією на **htmx** та адаптивним (мобільним) макетом.

## Як це працює

- `build.py` бере вміст наявних HTML-сторінок, обгортає його в спільний
  Jinja2-шаблон (`templates/base.html`) з SEO/Open Graph, htmx та мобільним
  меню, переписує посилання на чисті відносні URL і збирає `dist/`.
- Для кожної сторінки створюються **два** файли:
  - `dist/<slug>/index.html` — повна сторінка (прямий вхід, SEO, fallback без JS);
  - `dist/<slug>/fragment.html` — htmx-фрагмент (лише вміст), який підвантажується
    через `hx-get` без перезавантаження сторінки (`hx-push-url` оновлює URL).
- Внутрішні посилання мають і звичайний `href`, і htmx-атрибути — тож сайт
  працює і **без JavaScript** (звичайний перехід), і з htmx (SPA-навігація).
- GitHub Actions (`.github/workflows/pages.yml`) збирає й публікує `dist/` на
  Pages. Теку `dist/` не комітять.

## Збірка

```
pip install -r requirements.txt
python build.py       # -> dist/
python verify.py      # перевірка
python serve_test.py  # локальний HTTP-тест
```

## Структура

```
build.py            генератор (витягує вміст, htmx-навігація, SEO, OG)
config.py           домен, SEO, соцмережі
seo.py / slugs.py / og_image.py   SEO-голова, слаги, OG-зображення
templates/base.html спільний макет (head, мобільне меню, htmx)
templates/fragment.html  htmx-фрагмент
assets/media/       public.css, site.css, site.js, зображення, PDF
assets/fonts/       шрифт для OG-зображень
.github/workflows/  CI: збірка + публікація на Pages
```

## Мобільна адаптивність

- Коректний `viewport` (масштабування дозволене — прибрано `user-scalable=no`).
- Липке верхнє меню; на вузьких екранах — кнопка-гамбургер (`site.js`).
- `site.css` змушує фіксовані ширини конструктора переноситись на телефонах,
  зображення — `max-width:100%`.

## Форми

Сторінка «Вступ» (`/enrolling/`) містить вбудовану форму Tally.so.
Замініть `TALLY_ENROLL_ID` у `build.py` на ID вашої форми й перезберіть.

## Галерея

Динамічну галерею (яка тягла фото з LightUp) замінено на статичну сітку
зображень із `assets/media/images/`.
