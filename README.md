# Budget manager

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
