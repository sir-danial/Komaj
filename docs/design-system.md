# سیستم طراحی کماج (Komaj Design System)

> سند مرجع UI/UX برای فروشگاه کماج — پالت، تایپ، الگوها، و پلن توسعه فرانت.
> آخرین به‌روزرسانی: ۲۰۲۶-۰۴-۱۹
>
> **wireframe صفحات کلیدی**: [docs/wireframes.md](./wireframes.md)

---

## ۱. جهت طراحی

**نام**: _Persian Warmth_ — گرمای ایرانی مدرن
**ماهیت**: ترکیب حس بازار سنتی ایرانی (زعفران، پسته، کرم) با مینیمالیسم مدرن e-commerce.
**ضد-الگوها**: کیچ سنتی، شلوغی بازار، خشکی اپل، پالت سرد.
**احساس هدف**: دست‌ساز، اصیل، گرم، دعوت‌کننده — اما تمیز و سریع.

### سه گزینه ارزیابی شد
| گزینه | حس | تصمیم |
|-------|-----|-------|
| **A. گرمای ایرانی مدرن** | بازار + مینیمال، زعفرانی-پسته‌ای، الگوهای هندسی ظریف | ✅ انتخاب شد |
| B. مینیمال سفید | Applewsque، یک رنگ اکسنت | رد — سرد |
| C. هنری پررنگ | قهوه‌ای تیره + طلایی | رد — برای لوکس مناسب‌تر است تا سنتی-صمیمی |

---

## ۲. Moodboard — رفرنس‌ها

### ایرانی (شیرینی سنتی)
| سایت | درس |
|------|------|
| [Kolompeh Pastry](https://kolompehpastry.com) | فروشگاه خانوادگی کرمانی — همان «شیرینی سنتی با حس پریمیوم» |
| [Tavazo](https://tavazo.us/collections/confectionary-sweets) | بنر زعفران/پسته — اما UI شلوغ و قدیمی (درس منفی) |
| [Afrina Sweets](https://afrinasweets.com/) | Tagline "Taste of Persia" — زبان برندسازی |
| [ShopiPersia](https://shopipersia.com) | «natural ingredients, fragrant flavors» — لحن محصول |

### بین‌المللی (warm artisanal)
| سایت | الگو |
|------|-----|
| [Wildwood Bakery (Awwwards)](https://www.awwwards.com/inspiration/wildwood-bakery-illustrated-e-commerce-website) | illustrations نرم + تایپ بزرگ + پس‌زمینه کرم — نزدیک‌ترین رفرنس |
| [Swiss Organic Farm (Awwwards)](https://www.awwwards.com/sites/swiss-organic-farm) | parallax + texture طبیعی (کاغذ، کتان) |
| [Organic & Original Tastes (Awwwards)](https://www.awwwards.com/sites/organic-orignial-tastes) | مینیمال کرم + یک رنگ اکسنت گرم |

### الگوهای بصری مشترک
1. Hero گشاد با تصویر تمام‌عرض شیرینی روی سطح کرم + typography فارسی بزرگ
2. Product card با نسبت تصویر ۴:۵، حاشیه گرد ۱۶px، سایه نرم، badge وزن در گوشه
3. Texture طبیعی (کاغذ/کتان) به صورت subtle overlay با opacity 3-5%
4. فضای سفید زیاد — نه شلوغی بازار، نه سترون اپل
5. آیکون‌های illustrated کوچک (نه flat کامل) — دست‌ساز

---

## ۳. پالت رنگ

**اصل کلیدی**: زعفران **اکسنت** است، نه رنگ غالب. کرم/off-white اکثریت سطح را می‌گیرد و espresso لنگر متن است.

### رنگ‌های برند
| نقش | Hex | کاربرد |
|-----|-----|--------|
| `cream` | `#FAF6EE` | پس‌زمینه اصلی (~۸۵٪ سطح) |
| `espresso` | `#2E1F14` | متن اصلی — کنتراست AAA روی cream |
| `saffron` | `#C79A2C` | **اکسنت اصلی** — CTA، focal point، لوگو |
| `pistachio` | `#7A8B3D` | اکسنت ثانوی — badge، لینک، نشان تازگی |
| `pomegranate` | `#9C2B3B` | Pop — قیمت تخفیف، هشدار، sale tag |
| `sand` | `#F0E6D2` | کارت، divider، پس‌زمینه ثانوی |
| `soft-gold` | `#E8D4A2` | hover، badge طلایی روشن |

### States
| State | Hex | توضیح |
|-------|-----|-------|
| `success` | `#4A7C3C` (مشتق pistachio) | تایید سفارش |
| `warning` | `#D68A1A` (مشتق saffron) | هشدار موجودی |
| `error` | `#8E2430` (مشتق pomegranate) | خطای فرم |
| `info` | `#5A6F3A` | پیام خنثی |

### تغییرات نسبت به پیشنهاد اولیه
تحقیق نشان داد زعفران غالب = کیچ. پالت تعدیل شد:
| قبلی | جدید | دلیل |
|------|------|------|
| زعفران غالب | زعفران فقط CTA/accent | پرهیز از کیچ |
| `warm-brown #3A2418` | `espresso #2E1F14` | کنتراست AAA روی cream |
| الگوی هندسی همه‌جا | فقط corner بنر و footer | اشباع نشود |

### دارک مود
**فاز ۲.** در phase 1 فقط light mode. Tokens با CSS variables طراحی شود تا مهاجرت آسان باشد.

---

## ۴. Typography

### فونت اصلی: Vazirmatn
- **چرا**: variable font، ۹ weight، [Google Fonts](https://fonts.google.com/specimen/Vazirmatn) رایگان، خواناترین فونت فارسی وب در ۲۰۲۶
- **self-host** از [rastikerdar/vazirmatn](https://github.com/rastikerdar/vazirmatn) — سریع‌تر در ایران، بدون وابستگی به گوگل

### فونت تاکیدی: Lalezar (اختیاری)
برای hero/بنر خاص («شیرینی سنتی»، promo) — [Lalezar](https://fonts.google.com/specimen/Lalezar) حس retro/vintage می‌ده. فقط گاه‌گاه.

### مقیاس تایپ (Type Scale)
| Token | اندازه | weight | کاربرد |
|-------|--------|--------|--------|
| `display` | 48-64px | 800 | hero headline |
| `h1` | 32-40px | 700 | page title |
| `h2` | 24-28px | 700 | section title |
| `h3` | 20px | 600 | card title, subsection |
| `body-lg` | 18px | 500 | paragraph hero |
| `body` | 16px | 400 | متن پیش‌فرض |
| `body-sm` | 14px | 400 | caption, helper |
| `tiny` | 12px | 500 | badge, tag |
| `price` | — | 600, **tabular-nums** | همه قیمت‌ها |

### قوانین
- line-height: ۱.۷ برای body، ۱.۳ برای heading (فارسی نیاز به breathing بیشتر)
- letter-spacing: کمی منفی (-0.01em) روی heading بزرگ
- ارقام قیمت با `font-feature-settings: "tnum"` برای align
- **ارقام فارسی** (۰-۹) در همه اعداد نمایشی — با Django template filter

---

## ۵. اجزای بصری

### Spacing & Radius
```
spacing:  4px base grid (1 = 4px)
radius:   sm=6, md=12, lg=16, xl=24, full=9999
shadow:   subtle — sm=0 1 2 rgba(46,31,20,.05), 
          md=0 4 12 rgba(46,31,20,.08),
          lg=0 12 32 rgba(46,31,20,.10)
```

### Product Card
- نسبت تصویر: **4:5**
- radius: `xl` (24px)
- padding: `p-4`
- shadow: `sm` در حالت عادی، `md` روی hover
- badge وزن: گوشه بالا-راست، `sand` bg
- قیمت: `espresso`، tabular-nums، ارقام فارسی
- دکمه: `saffron` با متن `cream`

### Button (سه variant)
| Variant | bg | متن | border |
|---------|-----|-----|--------|
| primary | `saffron` | `cream` | - |
| secondary | `cream` | `espresso` | `espresso` 1px |
| ghost | transparent | `saffron` | - |

ارتفاع: `sm=36, md=44, lg=52`. radius: `md`. hover: brightness-95.

### Decoration
- Texture کتانی SVG با opacity 3-5% روی body
- الگوی هندسی اسلامی ظریف در corner بنر hero و footer (SVG)
- Illustration دستی کوچک (شاخه پسته، دانه زعفران) در section break

---

## ۶. Tokens (برای tailwind.config.js)

```js
// config/tailwind/tokens.js
export const colors = {
  cream:       '#FAF6EE',
  espresso:    '#2E1F14',
  saffron:     '#C79A2C',
  pistachio:   '#7A8B3D',
  pomegranate: '#9C2B3B',
  sand:        '#F0E6D2',
  'soft-gold': '#E8D4A2',
  success:     '#4A7C3C',
  warning:     '#D68A1A',
  error:       '#8E2430',
  info:        '#5A6F3A',
};

export const fontFamily = {
  sans:    ['Vazirmatn', 'system-ui', 'sans-serif'],
  display: ['Lalezar', 'Vazirmatn', 'serif'],
};

export const fontSize = {
  tiny:      ['12px', { lineHeight: '1.5', fontWeight: '500' }],
  'body-sm': ['14px', { lineHeight: '1.6' }],
  body:      ['16px', { lineHeight: '1.7' }],
  'body-lg': ['18px', { lineHeight: '1.7', fontWeight: '500' }],
  h3:        ['20px', { lineHeight: '1.4', fontWeight: '600' }],
  h2:        ['28px', { lineHeight: '1.3', fontWeight: '700' }],
  h1:        ['40px', { lineHeight: '1.2', fontWeight: '700' }],
  display:   ['56px', { lineHeight: '1.1', fontWeight: '800', letterSpacing: '-0.01em' }],
};

export const borderRadius = {
  sm: '6px', md: '12px', lg: '16px', xl: '24px',
};

export const boxShadow = {
  sm: '0 1px 2px rgba(46,31,20,.05)',
  md: '0 4px 12px rgba(46,31,20,.08)',
  lg: '0 12px 32px rgba(46,31,20,.10)',
};
```

### RTL config
```js
// tailwind.config.js
module.exports = {
  // ...
  content: ['./templates/**/*.html', './apps/**/templates/**/*.html'],
  theme: { extend: { ...tokens } },
  plugins: [],
  // استفاده از logical properties: ms-4 بجای ml-4، pe-5 بجای pr-5
};
```
`<html dir="rtl" lang="fa-IR">` در `base.html`.

---

## ۷. الزامات a11y

- همه رنگ‌ها روی `cream` با espresso متن → کنتراست AAA
- `saffron` روی cream → کنتراست AA (برای CTA کافی است، نه متن body)
- focus ring قابل دیدن: `ring-2 ring-saffron ring-offset-2 ring-offset-cream`
- همه aria-label فارسی، `lang="fa-IR"` روی html
- Skip link در ابتدای body
- تست با NVDA یا VoiceOver فارسی
- Lighthouse a11y ≥ 95، WCAG AA کل، AAA متن body

---

## ۸. پلن توسعه فرانت — ۲۸ روز موازی با backend

| فاز | مدت | خروجی | وابستگی |
|-----|-----|--------|---------|
| **A. Design tokens** | ۲ روز | `tailwind.config.js` با این tokens. self-host Vazirmatn. RTL فعال. logical properties. | شروع هر لحظه |
| **B. Typography + layout base** | ۱ روز | `base.html` + header skeleton + فیلتر ارقام فارسی | فاز A |
| **C. Primitive components** | ۴ روز | Button (۳ variant)، Input، Select، Badge، Card، Modal، Toast، Breadcrumb. Django template includes. | فاز A |
| **D. Header + Footer + Nav** | ۲ روز | سرچ، سبد (HTMX counter)، منو موبایل drawer، footer با لوگو اینماد/ساماندهی | فاز C |
| **E. Home + catalog** | ۵ روز | Hero، featured، لیست محصولات با فیلتر/pagination، صفحه جزئیات با گالری | نیاز به مدل‌های KOM-10 |
| **F. Cart + Checkout** | ۵ روز | سبد با HTMX، checkout چندمرحله‌ای، selector شهر، خلاصه | KOM-18, KOM-27 |
| **G. Auth (OTP UI)** | ۲ روز | فرم دومرحله‌ای با countdown، انیمیشن نرم | KOM-22, KOM-23 |
| **H. Account pages** | ۳ روز | داشبورد، سفارش‌های من، آدرس‌ها، دانلود فاکتور | KOM-33 |
| **I. Polish + a11y** | ۴ روز | focus، aria، Lighthouse > 90، WCAG AA، RTL regression | انتهای همه |

### ترتیب واقعی (ترکیب با پلن backend)
- **Week 2-3 (فعلی)**: A → B → C (tokens، base، primitives) — موازی با ساخت مدل‌های catalog
- **Week 3**: D + E (header + home + catalog) همراه با صفحات کاتالوگ backend
- **Week 4-5**: F + G (cart + OTP UI)
- **Week 7**: H (account) همراه با سفارش‌های من
- **Week 8**: I (polish) همراه با امنیت/لانچ

---

## ۹. ابزارها

| ابزار | نقش |
|-------|-----|
| Tailwind v3.4+ | CSS framework با RTL variants و logical properties |
| HTMX | تعامل بدون SPA — سبد، OTP، فیلتر، add-to-cart |
| Alpine.js | state کوچک client — drawer، dropdown (اختیاری) |
| heroicons یا phosphor | آیکون‌ست |
| Vazirmatn (self-host) | فونت اصلی |
| django-tailwind یا build standalone | pipeline |

**Storybook نصب نمی‌شود** — یک صفحه `/_styleguide/` در Django برای QA داخلی کافی است.

---

## ۱۰. اصول تصمیم‌گیری (در شک)

1. **کرم غالب، زعفران اکسنت** — هرگز زعفران را background بزرگ نکن
2. **فضای سفید سخاوتمندانه** — padding section ≥ 80px، gap ≥ 24px
3. **Logical properties** (`ms-*`, `pe-*`) — نه directional
4. **ارقام فارسی همیشه** برای اعداد نمایشی
5. **کنتراست AAA** برای متن body، AA حداقل برای هر چیز
6. **shadow نرم، نه تیز** — حس artisanal را کرمی نگه دارد
7. **Decoration subtle** — texture 3-5%، pattern فقط در corner

---

## ۱۱. منابع

### تحقیق فونت
- [Vazirmatn — Google Fonts](https://fonts.google.com/specimen/Vazirmatn)
- [rastikerdar/vazirmatn (GitHub)](https://github.com/rastikerdar/vazirmatn)
- [Lalezar — Google Fonts](https://fonts.google.com/specimen/Lalezar)

### تحقیق RTL
- [Tailwind CSS RTL — Flowbite](https://flowbite.com/docs/customize/rtl/)
- [Tailwind RTL Support — DEV](https://dev.to/themesberg/tailwind-rtl-support-for-ui-components-flowbite-9h)

### رفرنس‌های ایرانی
- [Kolompeh Pastry](https://kolompehpastry.com/)
- [Tavazo](https://tavazo.us/collections/confectionary-sweets)
- [Afrina Sweets](https://afrinasweets.com/)
- [ShopiPersia](https://shopipersia.com/)

### رفرنس‌های بین‌المللی
- [Wildwood Bakery (Awwwards)](https://www.awwwards.com/inspiration/wildwood-bakery-illustrated-e-commerce-website)
- [Swiss Organic Farm (Awwwards)](https://www.awwwards.com/sites/swiss-organic-farm)
- [Organic & Original Tastes (Awwwards)](https://www.awwwards.com/sites/organic-orignial-tastes)

### تحقیق پالت
- [Saffron Color Palette Guide — Piktochart](https://piktochart.com/tips/saffron-color-palette)
- [Food Color Palette Ideas — Media.io](https://www.media.io/color-palette/food-color-palette.html)
- [Top E-Commerce Design Trends 2026 — Fireart](https://fireart.studio/blog/top-e-commerce-website-design-trends/)
