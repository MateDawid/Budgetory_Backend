# Budget manager

0. **Project setup**
 	 - [ ] poetry
	 - [ ] Dockerfile
     - [ ] swagger
	 - [ ] PostgreSQL
     - [ ] docker-compose

1. **Data import** 
Module for file importing and saving its content as DB models instances.
 	 - [x] ~~ImportFile model, serializer, view~~
	 - [ ] Possibility to send file (csv firstly), but not storing it in DB, only extract data
	 - [ ] Validate file content
	 - [ ] Action to generate DB objects from file content
     - [ ] Tests

2. **Expenses**
Module for list of expenses.
	 - [ ] Expense model, serializer, view
	 - [ ] List of expenses on frontend side for each month
     - [ ] Tests

3. **Sellers**
Module for list of sellers / shops / providers billing user for expenses.
	 - [ ] Seller model, serializer, view
	 - [ ] List of Seller on frontend side
     - [ ] Tests

4. **Incomes**
Module for list of incomes.
	 - [ ] Income model, serializer, view
	 - [ ] List of incomes on frontend side for each month
     - [ ] Tests

5. **Deposits**
Module for list of places, where uses stores his/hers money.
	 - [ ] Deposit model, serializer, view
     - [ ] Tests

5. **Monthly plan** 
Module for creating budget plan for indicated month.
	 - [ ] MonthlyPlan model, serializer, view
	 - [ ] Creating expenses plan for each month
	 - [ ] Aggregating data from expenses and incomes endpoints
     - [ ] Tests
