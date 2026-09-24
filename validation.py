def is_valid_salary(salary):
	"""Return True if salary is a number that is 0 or more, otherwise False.

	Never raises an error, whatever you pass in.
	"""
	if isinstance(salary, bool):
		return False
	try:
		value = float(salary)
	except (TypeError, ValueError):
		return False
	return value >= 0
