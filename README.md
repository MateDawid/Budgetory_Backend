# Budget manager

## Predicted data flow

1. **User** creates **User** model instance (creates his/her own account).
2. **User** creates at least single **Deposit** model instance with Bank Account type, that will be connected with one of Bank model instances predefined by admin.
3. **User** saves his incomes in particular **ReportPeriod**: 
    - **User** defines all places of storing money (represented by **Deposit** model instances)
    - **User** adds **Income** model instances in context of **Deposit**
4. **User** saves **BudgetPlan** model instance for particular **ReportPeriod**:
    - User creates **ExpenseCategory** model instances
    - User updates every active **ExpenseCategory** inline in **BudgetPlan** with amount, that he/she plans to spent in particular **ReportingPeriod**
    - If **BudgetPlan** is created for more than one **User** every **ExpenseCategory** can be marked ass "Common" or belonging to particular User. Then app will calculate ammount, that every **User** should provide for common expenses. 
5. **User** saves his expenses in particular **ReportPeriod**:
    - **User** creates **ImportFile** model instance by uploading .csv file with expenses downloaded from his/her real bank account. File has to contain data about data, price, seller for every transaction.
    - Form filled with data from .csv file appears. User has possibility to correct sellers, change expense category and assign **ExpenseCategory** for every single **Expense**
    - **User** accepts form - not existing yet **Seller** model and **Expense** model instances are being created.
    - If **BudgetPlan** for particular **ReportingPeriod** exists, app updates **BudgetPlan** with uploaded **Expense** model instances data.
6. When there's no more data about incomes or expenses to upload, **User** closes **ReportPeriod**. It will also close **BudgetPlan**, that now will store report about success or failure of user's prediction.


## Models

1. User
2. ReportPeriod - month for which report will be calculated and presented
3. Bank
4. Deposit (with different types, "Bank Account" is a must)
5. Income
6. BudgetPlan - can be shared with many Users
7. ExpenseCategory - can be active/inactive, tree structure?
8. ImportFile - .csv file content with User expenses
9. Seller
10. Expense



## Steps to do

0. **Project setup**
	 - [x] ~~Python 3.11~~
 	 - [x] ~~poetry~~
	 - [ ] Dockerfile
     - [ ] swagger
	 - [ ] PostgreSQL
     - [ ] docker-compose


1. **Data import** 
Module for file importing and saving its content as DB models instances.
 	 - [x] ~~ImportFile model, serializer, view~~
	 - [x] ~~Possibility to send file (csv firstly), but not storing it in DB, only extract data~~
     - [x] ~~Tests~~
     - [ ] Frontend


2. **Sellers**
Module for list of sellers / shops / providers billing user for expenses.
	 - [ ] Seller model, serializer, view
     - [ ] Create sellers on data import
     - [ ] Tests 
     - [ ] Frontend


3. **Expenses**
Module for list of expenses.
	 - [ ] Expense model, serializer, view
     - [ ] Create expenses on data import
     - [ ] Tests
     - [ ] Frontend


4. **Incomes**
Module for list of incomes.
	 - [ ] Income model, serializer, view
     - [ ] Tests
	 - [ ] Frontend


5. **Deposits**
Module for list of places, where uses stores his/hers money.
	 - [ ] Deposit model, serializer, view
     - [ ] Tests
     - [ ] Frontend


6. **Monthly plan** 
Module for creating budget plan for indicated month.
	 - [ ] MonthlyPlan model, serializer, view
	 - [ ] Creating expenses plan for each month
	 - [ ] Aggregating data from expenses and incomes endpoints
     - [ ] Tests
     - [ ] Frontend
