import re

def movmean(A, k):
	"""
	https://www.mathworks.com/help/matlab/ref/movmean.html
	Specific implementation
	M = movmean(A,k) returns an array of local k-point mean values, where each
	mean is calculated over a sliding window of length k across neighboring
	elements of A. When k is odd, the window is centered about the element in
	the current position. When k is even, the window is centered about the
	current and previous elements. The window size is automatically truncated
	at the endpoints when there are not enough elements to fill the window.
	When the window is truncated, the average is taken over only the elements
	that fill the window. M is the same size as A.
		- If A is a vector, then movmean operates along the length of the
		vector A.
	This subroutine does not check if the input is a valid list of numbers.
	It is up to the caller to ensure the data is of the correct format.
	"""
	ret = []
	matrix_mode = False
	if len(A) == 0:
		return []
	for col in range(len(A)):
		sublist = A[max(0,col-k//2):col+k//2+k%2]
		ret += [sum(sublist)/len(sublist)]
	return ret

def preparecurvedata(list1, list2):
	"""
	https://www.mathworks.com/help/curvefit/preparecurvedata.html
	Specific implementation of most of the below:
	[XOut,YOut] = prepareCurveData(XIn,YIn) transforms data, if necessary, for
	curve fitting with the fit function. The prepareCurveData function
	transforms data as follows:
		- Return data as columns regardless of the input shapes. Error if the
		number of elements do not match. Warn if the number of elements match,
		but the sizes differ.
		- Convert complex to real (remove imaginary parts) and warn of this
		conversion.
		- Remove NaN or Inf from data and warn of this removal.
		- Convert nondouble to double and warn of this conversion.
	"""
	# data should be a list of numeric values, or numbers as strings
	# lists are by default used as arrays of numbers; there is no differentiation between rows and columns in python
	if type(list1) is not list or type(list2) is not list:
		raise Exception(f"Both inputs must be lists. type(list1): {type(list1)}; type(list2): {type(list2)}")
	# check if both lists have the same number of elements
	if len(list1) != len(list2):
		raise Exception(f"Both lists must have the same number of elements. len(list1): {len(list1)}; len(list2): {len(list2)}")
	# attempt to convert the list contents into numbers
	nan_flag = False
	inf_flag = True
	for elem in list1:
		# remove imaginary parts, NaN, and Inf from data
		# note that for NaN and Inf, the string value of the "elem" must be EXACTLY NaN or Inf (or -Inf)
		# for imaginary numbers, the string value must match the regex /^-?\d+(\.\d+)?(e[-+]?\d+)?([+-]\d+(\.\d+)?(e[-+]?\d+)?i)?$/
		nan_flag = nan_flag or str(elem) == "NaN"
		inf_flag = inf_flag or str(elem) in ["Inf", "-Inf"]
		try:
			#TODO
			pass
		except:
			pass
	if not all([type(elem) == float or type(elem) == int for elem in list1]):
		raise Exception("All list elements must be floats or integers: list1")
	if not all([type(elem) == float or type(elem) == int for elem in list2]):
		raise Exception("All list elements must be floats or integers: list2")
	# there is no need to convert complex to real since complex numbers cannot be represented as floats or integers
	# in a sense this is a specific implementation of preparecurvedata handling only lists of real values
	#####
	# TODO
	return list1, list2