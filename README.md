# Budget manager

## Models

1. User
2. BudgetingPeriod - month for which report will be calculated and presented
3. Bank
4. Deposit (with different types, "Bank Account" is a must)
5. Income
6. ExpenseCategory - can be active/inactive, tree structure?
7. Seller
8. Expense
9. ExpensePrediction
10. ImportFile - .csv file content with User expenses


## Predicted data flow

1. **User** creates **User** model instance (creates his/her own account).
2. **User** creates at least single **Deposit** model instance.
3. **User** creates **BudgetingPeriod** model instance.
4. **User** creates **Income** model instances in context of **Deposit** labeled with particular **BudgetingPeriod**.
5. **User** creates **ExpenseCategory** model instances.
6. **User** creates **ExpensePrediction** model instances - amount, that **User** plans to spent in particular **BudgetingPeriod** on indicated **ExpenseCategory**.
7. **User** creates **ImportFile** model instance by:
   * Uploading .csv file with expenses downloaded from his/her real bank account. File has to contain data about data, price, seller for every transaction.
       - Form filled with data from .csv file appears. User has possibility to correct sellers, change expense category and assign **ExpenseCategory** for every single **Expense**
       - **User** accepts form - not existing yet **Seller** model and **Expense** model instances are being created.
   * **User** creates **Expense** model instances manually
8. When there's no more data about incomes or expenses to add in particular **BudgetingPeriod**, **User** closes it.


## Steps to do

1. ✔️ ~~**Project setup**~~
   - [x] ~~Python 3.11~~
   - [x] ~~poetry~~
   - [x] ~~pre-commit~~
   - [x] ~~Dockerfile~~
   - [x] ~~docker-compose~~
   - [x] ~~Documentation (f.e. Swagger)~~
   - [x] ~~PostgreSQL~~
   - [x] ~~GitHub Actions~~

2. ✔️ ~~**User**~~
   - [x] ~~User model~~
   - [x] ~~User serializer~~
   - [x] ~~User view~~
   - [x] ~~User tests~~

3. ✔️ ~~**BudgetingPeriod**~~
   - [x] ~~BudgetingPeriod model~~
   - [x] ~~BudgetingPeriod serializer~~
   - [x] ~~BudgetingPeriod views~~
   - [x] ~~Tests~~

4. 🔨 **Deposits**
   - [ ] Deposit model, serializer, view
   - [ ] Tests

5. 🔜 **Incomes**
   - [ ] Income model, serializer, view
   - [ ] Tests

6. 🔜 **Sellers**
   - [ ] Seller model, serializer, view
   - [ ] Tests

7. 🔜 **ExpenseCategory**
   - [ ] ExpenseCategory model, serializer, view
   - [ ] Tests

8. 🔜 **Expenses**
   - [ ] Expense model, serializer, view
   - [ ] Create expenses on data import
   - [ ] Tests

9. 🔜 **ExpensePrediction**
   - [ ] ExpensePrediction model, serializer, view
   - [ ] Tests

10. 🔜 **ImportFile**
    - [ ] ImportFile model, serializer, view
    - [ ] Possibility to send file (csv firstly), but not storing it in DB, only extract data
    - [ ] Create sellers on data import
    - [ ] Tests

11. 🔜 **Frontend**
    - [ ] Implement some frontend
