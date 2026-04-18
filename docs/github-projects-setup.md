# راه‌اندازی GitHub Projects v2 و آپدیت خودکار

این سند نحوه فعال‌سازی بورد Projects v2 و اتصال آن به GitHub Actions برای آپدیت خودکار وضعیت آیتم‌ها را توضیح می‌دهد. تا زمانی که این مراحل طی نشود، مدیریت پیشرفت از طریق **Issues + Milestones** انجام می‌شود که از قبل فعال است.

## وضعیت فعلی

- ۸ **Milestone** ساخته شده (هفته ۱ تا هفته ۸) با due dateهای هفتگی
- ۲۶ **Issue** برای تسک‌های رودمپ (در [issues](https://github.com/sir-danial/Komaj/issues))
- مجموعه **labels** استاندارد: `area:*`, `P0-critical`/`P1-high`/`P2-nice-to-have`, `type:*`, `status:blocked`
- **CI workflow** (`.github/workflows/ci.yml`) روی هر PR/push اجرا می‌شود
- بستن خودکار Issues با keyword `Closes #N` در PR (built-in GitHub)

## برای فعال‌سازی Projects v2

### قدم ۱ — scope اضافه برای gh CLI (یک‌بار)

در ترمینال خودت:

```sh
gh auth refresh -s project
```

مرورگر باز می‌شود، کد را وارد کن و تایید کن.

### قدم ۲ — ساخت Personal Access Token (PAT)

GITHUB_TOKEN داخل Actions به Projects v2 دسترسی ندارد. باید یک fine-grained PAT بسازی:

1. برو به https://github.com/settings/personal-access-tokens/new
2. تنظیمات:
   - **Token name**: `Komaj Projects Sync`
   - **Expiration**: ۹۰ روز (بعداً قابل تمدید)
   - **Resource owner**: `sir-danial`
   - **Repository access**: Only select repositories → `Komaj`
   - **Permissions**:
     - Repository: `Issues: Read/Write`, `Pull requests: Read`, `Metadata: Read (auto)`
     - Account: `Projects: Read/Write`
3. کلیک روی **Generate token** و کپی مقدار
4. برو به `https://github.com/sir-danial/Komaj/settings/secrets/actions`
5. کلیک **New repository secret**:
   - Name: `PROJECTS_TOKEN`
   - Secret: (مقدار کپی شده)

### قدم ۳ — ساخت Project v2

```sh
gh project create --owner sir-danial --title "Komaj Roadmap"
# خروجی شامل شماره پروژه است، مثلاً: https://github.com/users/sir-danial/projects/3
```

شماره پروژه (مثلاً `3`) را یادداشت کن.

### قدم ۴ — اضافه کردن فیلدهای سفارشی

از رابط وب پروژه این فیلدها را اضافه کن (فیلد Status و Title به‌صورت پیش‌فرض وجود دارد):

| نام فیلد | نوع | گزینه‌ها |
|---------|-----|---------|
| **Week** | Single select | Week 1, Week 2, …, Week 8 |
| **Priority** | Single select | P0, P1, P2 |
| **Area** | Single select | setup, catalog, cart, payment, shipping, auth, admin, seo, security, external, docs |

### قدم ۵ — اضافه کردن همه Issueهای موجود به Project

```sh
PROJECT_NUMBER=3  # شماره پروژه خودت
OWNER="sir-danial"

gh issue list --repo sir-danial/Komaj --state all --limit 50 --json url -q '.[].url' | \
  while read url; do
    gh project item-add $PROJECT_NUMBER --owner $OWNER --url "$url"
  done
```

### قدم ۶ — Workflow همگام‌سازی خودکار

فایل `.github/workflows/project-sync.yml` را با محتوای زیر بساز:

```yaml
name: Project Sync

on:
  issues:
    types: [opened, reopened, closed]
  pull_request:
    types: [opened, reopened, closed]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    if: github.event.action == 'opened' || github.event.action == 'reopened'
    steps:
      - uses: actions/add-to-project@v1.0.2
        with:
          project-url: https://github.com/users/sir-danial/projects/3
          github-token: ${{ secrets.PROJECTS_TOKEN }}

  set-in-progress:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' && github.event.action == 'opened'
    steps:
      - name: Set linked issues to In Progress
        uses: leonsteinhaeuser/project-beta-automations@v2.2.1
        with:
          gh_token: ${{ secrets.PROJECTS_TOKEN }}
          user: sir-danial
          project_id: 3
          resource_node_id: ${{ github.event.pull_request.node_id }}
          status_value: "In Progress"

  set-done:
    runs-on: ubuntu-latest
    if: github.event.action == 'closed' && (github.event.pull_request.merged == true || github.event_name == 'issues')
    steps:
      - name: Set to Done
        uses: leonsteinhaeuser/project-beta-automations@v2.2.1
        with:
          gh_token: ${{ secrets.PROJECTS_TOKEN }}
          user: sir-danial
          project_id: 3
          resource_node_id: ${{ github.event.issue.node_id || github.event.pull_request.node_id }}
          status_value: "Done"
```

> **نکته:** جایگزین `3` در `project_id` و URL با شماره پروژه واقعی خودت.

commit و push کن؛ از بعد از آن:
- هر issue/PR جدید → خودکار اضافه به بورد با Status=Todo
- PR باز شود → Issue مرتبط به In Progress
- PR merge یا issue بسته شود → Done

### قدم ۷ (اختیاری) — پر کردن Week بر اساس Milestone

این با script یک‌باره قابل انجام است:

```sh
# map milestone title → Week field option
# استفاده از gh api graphql برای به‌روزرسانی field items
# مثال در: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
```

می‌توانیم بعداً این را در یک management command Django یا workflow اضافه کنیم.

## نقشه وظایف فعلی

پیشرفت رودمپ را از این روش‌ها می‌توانی دنبال کنی:

1. **Milestones**: https://github.com/sir-danial/Komaj/milestones — پیشرفت هفتگی
2. **Issues per milestone**: مثلاً [Week 2](https://github.com/sir-danial/Komaj/issues?q=is%3Aissue+milestone%3A%22Week+2+%E2%80%94+Data+models+%26+admin%22)
3. **Labels**: [area:payment](https://github.com/sir-danial/Komaj/labels/area%3Apayment) یا [P0-critical](https://github.com/sir-danial/Komaj/labels/P0-critical)
4. **CI status**: https://github.com/sir-danial/Komaj/actions

بعد از فعال‌سازی Projects v2، یک نمای اضافه روی بورد با Week و Area و Status خواهی داشت.
