# Budgetory Backend

Django REST Framework API powering the **Budgetory** personal finance management application, consumed by the [Budgetory Frontend](https://github.com/MateDawid/Budgetory_Frontend) React client.

---

## Tech Stack

| | |
|---|---|
| **Language** | Python 3.12 |
| **Framework** | Django + Django REST Framework |
| **Dependency Management** | Poetry |
| **Database** | PostgreSQL |
| **Configuration** | Dynaconf |
| **Code Quality** | Pre-commit hooks, Flake8 |
| **Containerisation** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Features

### 🔐 User Authentication
Token-based authentication system ensuring secure access to the API. Each user's data is fully isolated — wallets, periods, deposits, categories, and transfers are scoped to the authenticated user. Supports registration, login, logout, and demo login.

---

### 📊 Dashboard Data Aggregation
The API provides computed endpoints that aggregate financial data for dashboard display. These endpoints calculate key metrics such as total income and expenses for the current period, deposit balances across wallets, and progress tracking against expense predictions — delivering real-time financial summaries.

---

### 👛 Wallets
API endpoints for managing wallets that organize multiple deposits under a common purpose. Each wallet can contain its own periods, deposits, and transfer history, enabling users to maintain separate budgets (e.g., daily spending vs. long-term savings). Supports CRUD operations with user-scoped isolation.

---

### 📅 Periods
API for managing periods that represent time ranges (e.g. monthly or custom date ranges) during which financial activity is tracked. Each period acts as a container for incomes, expenses, and predictions. The API enforces that periods cannot overlap within the same wallet and handles cascading deletion of related data.

---

### 💳 Deposits
CRUD operations for deposit accounts within wallets. Each deposit tracks a balance that is automatically calculated and updated based on linked transfers. The API maintains real-time balance accuracy across all deposits and supports filtering by wallet and period.

---

### 🏢 Entities
API for managing entities that represent external parties involved in financial transactions (employers, shops, service providers, individuals). Entities can be associated with income or expense transfers to track money flow sources and destinations. Supports user-specific entity management with validation to prevent deletion of entities referenced by existing transfers.

---

### 🏷️ Categories
CRUD operations for income and expense categories used to classify transfers. Categories are user-specific and each has a type (`income` or `expense`). The API prevents deletion of categories that are referenced by existing transfers to maintain data integrity.

---

### 🔮 Expense Predictions
API for setting and managing predicted spending amounts for expense categories within periods. Predictions are unique per category per period and allow tracking of predicted versus actual spending. Only expense categories can have predictions. The API provides comparison endpoints for budget adherence monitoring.

---

### 💰 Incomes
Income transfer management API supporting creation, retrieval, updating, and deletion of income entries. Each income is linked to a category, deposit, period, and optionally a source entity. The API supports filtering by period and provides full transfer history with automatic deposit balance updates.

---

### 💸 Expenses
Expense transfer management API supporting creation, retrieval, updating, and deletion of expense entries. Each expense is linked to a category, deposit, period, and optionally a target entity. The API supports filtering by period, comparison against predictions for budget tracking, and automatic deposit balance updates.

---

## API Documentation

> **Swagger/OpenAPI documentation** will be available once the application is deployed.

---

## Related Repositories

| Repository | Description |
|---|---|
| [Budgetory_Frontend](https://github.com/MateDawid/Budgetory_Frontend) | React client consuming this API |

---

## Author

**Dawid Mateusiak** — [@MateDawid](https://github.com/MateDawid)