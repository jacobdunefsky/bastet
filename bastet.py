import enum
import collections
import sys
import csv

#BaSTet: BAsic Static TEmplaTes

class ExprTypes(enum.Enum):
	FUNC = 1
	VAR = 2
	NUM = 3
	STR = 4
	# dumb hack for binary index dot
	VAL = 5

# note that the 0th arg is the name of the function
FuncExpr = collections.namedtuple("FuncExpr", ['expr_type', 'func_expr_args'])
# var_name: a single identifier
VarExpr = collections.namedtuple("VarExpr", ['expr_type', 'var_expr_name'])
# value of a NumExpr is the number AS A STRING
NumExpr = collections.namedtuple("NumExpr", ['expr_type', 'num_expr_value'])
StrExpr = collections.namedtuple("StrExpr", ['expr_type', 'str_expr_value'])
ValExpr = collections.namedtuple("ValExpr", ['expr_type', 'val_expr_value'])

binary_ops = ['+', '==', '@']

class BastetError(Exception):
	def __init__(self, msg, offender):
		self.msg = msg
		self.offender = offender
		super().__init__(str(msg) + ": " + str(offender))

def error(msg, offender):
	raise BastetError(msg, offender)

def expr_process(expr):	
	expr = expr.strip() #remove leading/trailing whitespace

	if len(expr) == 0:
		#no null expressions
		error("null expression", expr)

	# match against binary operators
	in_str = False
	paren_level = 0
	for i in range(len(expr)):
		#TODO: currently, all binary operators are by default right-associative
		if not in_str:
			if expr[i] == "\"":
				in_str = True
				continue
		if in_str:
			if expr[i] == "\"":
				in_str = False
			continue
		# not in string
		if expr[i] == "(":
			paren_level += 1
			continue
		if expr[i] == ")":
			paren_level -= 1
			continue
		if paren_level == 0:
			for op in binary_ops:
				if expr[i:i+len(op)] == op:
					func_expr = FuncExpr(expr_type=ExprTypes.FUNC,\
						func_expr_args=[op, expr[:i],expr[i+len(op):]])
					return func_expr
			if expr[i] == '.':
				# dumb unnecessary quadratic time
				j = i+1
				while j < len(expr) and expr[j].isidentifier(): j += 1
				b_str = expr[i+1:j]

				# dumb hack to deal with floats
				# TODO: make this better
				if b_str == '': continue

				a_str = expr[:i]

				a_val = expr_eval(a_str)
				if a_val.value_type != ValueTypes.TABLE and\
					a_val.value_type != ValueTypes.DICT:
					error("attempted to access field not\
						belonging to a table or dict", expr)

				try:
					#hack: a_val[1], no matter a_val's type, is always the
					#	actual value contained in a_val
					retval = a_val[1][b_str]
				except KeyError:
					print(a_str)
					print(b_str)
					error("field not found", expr)

				return ValExpr(expr_type=ExprTypes.VAL,val_expr_value=retval)

	if expr[0] == "(":
		if expr[-1] != ")":
			error("no closing paren", expr)
		return expr_process(expr[1:-1])
			
	if expr[0] == "$":
		#expression is a variable
		#check that variable name isn't empty
		if len(expr) == 1:
			error("empty var name", expr)

		var_info = expr[1:]

		#check that each field is a valid identifier
		if not var_info.isidentifier():
			print(i)
			error("bad var name", expr)

		var_expr = VarExpr(expr_type=ExprTypes.VAR,\
			var_expr_name=var_info)
		return var_expr
	if expr[0].isdigit():
		#expression is a numeric literal
		#check for at most one decimal point
		num_info = expr.split(".")
		if len(num_info) > 2:
			error("multiple decimal points", expr)

		#check that all our characters are digits
		for i in num_info:
			if not i.isdigit():
				error("non-numeric characters", expr)

		num_expr = NumExpr(expr_type=ExprTypes.NUM,\
			num_expr_value=expr)
		return num_expr
	if expr[0] == "\"":
		# expression is a string literal

		#check that string has at least two characters
		if len(expr) == 1:
			error("bad string", expr)

		#check that our string has a closing quote
		if not expr[-1] == "\"":
			error("no closing quote", expr)

		#check that we have precisely two quotes
		#note that right now, strings aren't allowed to contain escapes

		if "\"" in expr[1:-1]:
			error("too many quotes", expr)

		str_expr = StrExpr(expr_type=ExprTypes.STR, str_expr_value=expr[1:-1])
		return str_expr
	if expr[0].isidentifier():
		# expression is a function name

		# check that our function is actually a function
		# (and not just a variable that the user forgot to stick a $ on)
		i = expr.find("(")
		if i == -1:
			error("malformed identifier", expr)

		# check that our function has a closing paren
		if not expr[-1] == ")":
			error("no closing paren", expr)

		func_name = expr[0:i]

		#check that our function name is valid
		if not func_name.isidentifier():
			error("bad function name", func_name)

		arg_str = expr[i+1:-1]

		func_info = [func_name]

		#split up args
		#note that we can't get away with simply calling split(","), because
		#	commas might be present in string literals

		i += 1
		arg_start = i
		in_str = False

		while i < len(expr)-1:
			if expr[i] == "\"":
				# remember: no escapes
				in_str = not in_str
			if expr[i] == "," and not in_str:
				#see a comma, split our args
				cur_arg = expr[arg_start:i]
				func_info.append(cur_arg)
				#i+=1
				arg_start = i + 1
			i += 1

		func_info.append(expr[arg_start:-1])

		return FuncExpr(expr_type=ExprTypes.FUNC, func_expr_args=func_info)

	# default case
	return ("ERROR", ["INVALID_EXPR"])

class ValueTypes(enum.Enum):
	NUM = 1
	STR = 2
	LIST = 3
	TABLE = 4
	DICT = 5

NumValue = collections.namedtuple("NumValue", ['value_type', 'num_value'])
StrValue = collections.namedtuple("StrValue", ['value_type', 'str_value'])
ListValue = collections.namedtuple("ListValue", ['value_type', 'list_value'])
TableValue = collections.namedtuple("TableValue", ['value_type', 'table_value'])
DictValue = collections.namedtuple("DictValue", ['value_type', 'dict_value'])

func_dict = {}
root_var = DictValue(value_type=ValueTypes.DICT, dict_value={})

# stack of root_vars
# necessary in order to implement variable scope
context = [root_var]

# functions for setting and getting variables
def set_var(var_name, var_value):
	if not var_name.isidentifier():
		error("not an identifier", str(var_name))
	try:
		if var_value.value_type not in ValueTypes:
			error("when assigning to "+ str(var_name) + "not a value:", var_value)
	except AttributeError:
		error("when assigning to "+ str(var_name) + "not a value:", var_value)
	context[-1].dict_value[var_name] = var_value
def get_var(var_name):
	if not var_name.isidentifier():
		error("not an identifier", str(var_name))
	for var_dict in reversed(context):
		try:
			return var_dict.dict_value[var_name]
		except KeyError:
			continue
	error("variable not assigned:", var_name)
# functions for managing scope
def new_scope_frame():
	context.append(DictValue(value_type=ValueTypes.DICT, dict_value={}))
def del_scope_frame():
	assert(len(context) > 1)
	context.pop()

def expr_eval(expr_str):
	# first, process current expression
	expr = expr_process(expr_str)

	#I'm splitting these into different cases in order to futureproof
	if expr.expr_type == ExprTypes.NUM:
		# deal with floats
		# the >= 2 decimal point case is dealt with in expr_process
		if expr.num_expr_value.count('.') == 1:
			return NumValue(value_type=ValueTypes.NUM,\
				num_value=float(expr.num_expr_value))
		if expr.num_expr_value.count('.') == 0:
			return NumValue(value_type=ValueTypes.NUM,\
				num_value=int(expr.num_expr_value))
		else:
			error("?????", expr_str)
	if expr.expr_type == ExprTypes.STR:
		return StrValue(value_type=ValueTypes.STR,\
			str_value=expr.str_expr_value)

	if expr.expr_type == ExprTypes.FUNC:
		# this is where we get into the good stuff
		args = []
		for i in expr.func_expr_args[1:]:
			# evaluate each function arg
			args.append(expr_eval(i))
		# look up the function referenced in expr and call it on args
		try:
			retval = func_dict[expr.func_expr_args[0]](args)
		except KeyError:
			error("function not defined", expr_str)
		return retval
	
	if expr.expr_type == ExprTypes.VAR:
		#print(processed)
		"""cur_var = root_var
		# var format: (type, data)
		for i in expr.var_expr_names:
			if cur_var.value_type == ValueTypes.DICT:
				my_value = cur_var.dict_value
			elif cur_var.value_type == ValueTypes.TABLE:
				my_value = cur_var.table_value
			else:
				error("attempted to index non-dict or table", expr_str)
			try:
				cur_var = my_value[i]
			except KeyError:
				error("name %s not defined" % i, expr_str)"""
		try:
			#return root_var.dict_value[expr.var_expr_name]
			return get_var(expr.var_expr_name)
		except KeyError:
			error("name %s not defined" % i, expr_str)

	if expr.expr_type == ExprTypes.VAL:
		return expr.val_expr_value


# HERE BE builtin functions

def table_load(args):
	# parses a CSV file (using python's builtin parser -- I'm lazy)
	#	and returns a corresponding TABLE value
	# a TABLE is essentially a 2D array with named columns
	# internally, a TABLE is stored as a dict of arrays, where each array is
	#	 of the form ("LIST", array)

	# one arg: filename

	if len(args) != 1:
		error("table_load expects 1 arg; " + str(len(args)) + " given", "")

	path = args[0]
	
	if path.value_type != ValueTypes.STR:
		error("table_load takes a string as argument", "")

	try:
		table_file = open(path.str_value, "r")
	except FileNotFoundError:
		error("path not found in table_load", path.str_value)

	reader = csv.reader(table_file)

	# we're not gonna use DictReader here because we need custom error checking
	# (in addition to other things)
	try:
		header_row = next(reader)
		# header_row gives us our column names
	except StopIteration:
		error("table lacks a header row", path.str_value)

	# check for duplicate column names
	# there's definitely a faster way to do it, but it's not worth thinking
	#	about now
	occs = {}
	for i in header_row:
		occs[i] = 0
	for i in header_row:
		occs[i] += 1
		if occs[i] != 1:
			error("table has header row with duplicate column names",\
				path.str_value)


	ret_table = TableValue(value_type=ValueTypes.TABLE, table_value={})

	for i in header_row:
		ret_table.table_value[i] = ListValue(value_type=ValueTypes.LIST,\
			list_value=[])

	#row_count = 0

	for row in reader:
		s = min(len(header_row), len(row))
		for i in range(s):
			ret_table.table_value[header_row[i]].list_value.append(row[i])
		for i in range(s, len(header_row)):
			# deal with columns that have no value
			# note that when a row has more columns than the header row, we
			#	simply ignore the extra values
			ret_table.table_value[header_row[i]].list_value.append(None)
		#row_count += 1

	return ret_table

def get_len(args):
	a = args[0]
	if a.value_type == ValueTypes.TABLE:
		retval = len(a.table_value[list(a.table_value)[0]].list_value)
	elif a.value_type == ValueTypes.LIST:
		#print("my list... " + str(a))
		retval = len(a.list_value)
		#print("retval... " + str(retval))
	else:
		error("len requires a table or list", args)
	return NumValue(value_type=ValueTypes.NUM, num_value=retval)

def table_get_row(table, row):
	# typechecking
	if table.value_type != ValueTypes.TABLE:
		# we should never see this message -- such errors should be caught
		#	before this point
		error("attempted to get row of a non-table??", table)
	
	retrow = {} #note that our "row" is actually a dict

	# we should ideally make sure that all column names are unique
	# however, currently, the only expression that returns a table is
	#	table_load, and table_load does this check for us
	# this is not futureproof, but I'll leave the fix as an exercise
	# to my future self

	for i in table.table_value:
		#loop through columns
		try:
			retrow[i] = StrValue(value_type=ValueTypes.STR,\
				str_value=table.table_value[i].list_value[row])
		except IndexError:
			error("row " + str(row) + " is out of range for table", table)

	return DictValue(value_type=ValueTypes.DICT, dict_value=retrow)

def make_list(args):
	return ListValue(value_type=ValueTypes.LIST, list_value=args)

def add(args):
	# "+" binary operator
	# operates on num and string
	# if both are num, returns num
	# otherwise returns string
	a = args[0]
	b = args[1]
	if not ((a.value_type == ValueTypes.STR or a.value_type == ValueTypes.NUM)\
		and (b.value_type == ValueTypes.STR or b.value_type == ValueTypes.NUM)):
		error("invalid type for add", args)

	# hack: second element of value tuple is always that value
	a_val = a[1]
	b_val = b[1]
	if a.value_type == ValueTypes.STR or b.value_type == ValueTypes.STR:
		a_val = str(a_val)
		b_val = str(b_val)
		return StrValue(value_type=ValueTypes.STR, str_value=a_val + b_val)
	if isinstance(a_val, float) or isinstance(b_val, float):
		a_val = float(a_val)
		b_val = float(b_val)
	else:
		a_val = int(a_val)
		b_val = int(b_val)
	return NumValue(value_type=ValueTypes.NUM, num_value=a_val + b_val)

def index(args):
	# "@" binary operator
	# in this templating language, array indexing uses "@" because it's easier to code
	# operates on array and num
	a = args[0]
	b = args[1]
	if b.value_type != ValueTypes.NUM or isinstance(b.num_value, float):
		error("array index requires integer", args)
	if a.value_type == ValueTypes.LIST:
		return a.list_value[int(b.num_value)]
	if a.value_type == ValueTypes.TABLE:
		return table_get_row(a, int(b.num_value))
	error("array index requires either table or list", args)

def equals(args):
	a = args[0]
	b = args[1]
	if a == b:
		return NumValue(value_type=ValueTypes.NUM, num_value=1)
	else:
		return NumValue(value_type=ValueTypes.NUM, num_value=0)

#END builtin functions

# load our builtin functions into func_dict
func_dict["table_load"] = table_load
func_dict["list"] = make_list
#binary funcs
func_dict["+"] = add
func_dict["@"] = index
func_dict["=="] = equals

# block processing

class BlockTypes(enum.Enum):
	RAW = 1
	CODE = 2

# note that the 0th arg is the name of the function
RawBlock = collections.namedtuple("RawBlock", ['block_type', 'raw_block_value', 'block_linenum'])
CodeBlock = collections.namedtuple("CodeBlock", ['block_type', 'code_block_value', 'block_linenum'])

def blockify(text):
	blocks = []

	in_code = False
	in_str = False
	i = 0
	block_start = 0
	linenum = 0
	while i < len(text):
		if text[i] == "\n":
			linenum += 1
		if text[i:i+2] == "{%":
			if not in_code:
				cur_block = text[block_start:i]

				blocks.append(RawBlock(block_type=BlockTypes.RAW,\
					raw_block_value=cur_block, block_linenum=linenum))

				in_code = True
				i += 2
				block_start = i
				continue
			elif not in_str:
				# no nested {% allowed
				error("Nested code opening tag", text)
		if text[i:i+2] == "%}":
			if in_code:
				if not in_str:
					cur_block = text[block_start:i]
					
					blocks.append(CodeBlock(block_type=BlockTypes.CODE,\
						code_block_value=cur_block, block_linenum=linenum))

					in_code = False
					i += 2
					block_start = i
					continue
		if text[i] == "\"":
			if in_code:
				if in_str:
					in_str = False
				else:
					in_str = True
		i += 1
	if in_code:
		blocks.append(CodeBlock(block_type=BlockTypes.CODE,\
			code_block_value=text[block_start:], block_linenum=linenum))
	else:
		blocks.append(RawBlock(block_type=BlockTypes.RAW,\
			raw_block_value=text[block_start:], block_linenum=linenum))
	return blocks

# block evaluation helper funcs

def get_stmt(block):
	if block.block_type != BlockTypes.CODE:
		error("block type not code in get_stmt", block)
	code = block.code_block_value.strip()
	first_space = code.find(" ")
	if first_space == -1: return code
	return code[:first_space]

def get_stmt_expr(block, pos=1):
	if block.block_type != BlockTypes.CODE:
		error("block type not code in get_stmt_expr", block)

	code = block.code_block_value.strip()
	first_space = code.find(" ")
	if first_space == -1: return ""
	retval = code[first_space+1:]
	if pos == 1: return retval
	return get_stmt_expr(
		CodeBlock(block_type=BlockTypes.CODE, code_block_value=retval,\
			block_linenum=block.block_linenum),
		pos-1)

def get_stmt_arg(block, arg_num):
	if block.block_type != BlockTypes.CODE:
		error("block type not code in get_stmt_arg", block)
		
	code = block.code_block_value.strip()

	i = 0
	arg_start = i
	in_str = False

	cur_arg_num = 0

	while i < len(code):
		if code[i] == "\"":
			# no escapes in this language
			in_str = not in_str
		if code[i] == " " and not in_str:
			#see a space, split our args
			if cur_arg_num == arg_num:
				return code[arg_start:i]

			arg_start = i
			cur_arg_num += 1
		i += 1

	if cur_arg_num == arg_num:
		return code[arg_start:]

	return None

def is_raw(block):
	return block.block_type == BlockTypes.RAW

def block_eval(blocks):
	retlist = []
	for i in range(len(blocks)):
		try:
			block = blocks[i]
			if block.block_type == BlockTypes.RAW:
				retlist.append(block.raw_block_value)
				continue
			#block is a statement
			cur_stmt = get_stmt(block)

			if cur_stmt == "include":
				#todo: error handling after everything
				#check number of args, all that jazz
				incl_arg = get_stmt_arg(block, 1)
				incl_path = expr_eval(incl_arg)
				if not incl_path.value_type == ValueTypes.STR:
						error("include requires a string", cur_stmt)
				pathname = incl_path.str_value
				try:
					incl_file = open(pathname, "r")
				except FileNotFoundError:
					error("invalid path in include", cur_stmt)
				incl_blocks = blockify(incl_file.read())
				#print(incl_blocks)
				retlist.extend(block_eval(incl_blocks))
				continue

			if cur_stmt == "echo":
				echo_arg = get_stmt_expr(block) #was get_stmt_arg(block, 1)
				echo_expr = expr_eval(echo_arg)
				# hack; value of an expression is always its second member
				retlist.append(str(echo_expr[1]))
				continue

			if cur_stmt == "set":
				set_var_str = get_stmt_arg(block, 1)
				set_var_expr = expr_process(set_var_str)
				if set_var_expr.expr_type != ExprTypes.VAR:
					error("set takes a variable", block)
				set_arg = get_stmt_expr(block, 2)
				set_val = expr_eval(set_arg)
				# store variable in the dict of variables
				# note: if we have "set $foo.bar baz", then we assign
				#	baz to $foo, not $foo.bar

				#root_var.dict_value[set_var_expr.var_expr_name] = set_expr
				set_var(set_var_expr.var_expr_name, set_val)
				continue

			# block statements
			
			if cur_stmt == "for":
				new_scope_frame()
				# TODO: add error checking

				if get_stmt_arg(block, 2).strip() != "in":
					#print(get_stmt_arg(block, 2))
					error("invalid for loop syntax", block)

				loop_var_str = get_stmt_arg(block, 1)
				loop_var_expr = expr_process(loop_var_str)
				if loop_var_expr.expr_type != ExprTypes.VAR:
					error("for loop takes a variable", block)

				table_str = get_stmt_arg(block, 3)
				table_val = expr_eval(table_str)

				if not (table_val.value_type == ValueTypes.TABLE\
					or table_val.value_type == ValueTypes.LIST):
					print(table_val)
					error("for loop requires table or list", block)

				# figure out the scope of this loop

				loop_level = 1

				j = i+1
				while j < len(blocks):
					inner_block = blocks[j]
					if is_raw(inner_block):
						j += 1
						continue
					inner_stmt = get_stmt(inner_block)
					if inner_stmt == "for":
						loop_level += 1
					if inner_stmt == "endfor":
						# note: no error checking regarding format of endfor stmt
						loop_level -= 1
					if loop_level == 0:
						break
					j += 1
				if not loop_level == 0:
					error("for loop isn't closed", block)

				retval = ""

				for k in range(get_len([table_val]).num_value):
					# note: if we have "for $foo.bar in baz", then the loop assigns
					#	the current row to $foo, not $foo.bar
					#print("loop var arg... " + loop_var_arg[1][0])

					# loop differently depending on whether we're in a table or a list
					#print("table expr... " + str(table_expr))
					if table_val.value_type == ValueTypes.TABLE:
						#root_var.dict_value[loop_var_expr.var_expr_name]\
						#	= table_get_row(table_val, k)
						set_var(loop_var_expr.var_expr_name, table_get_row(table_val, k))
					if table_val.value_type == ValueTypes.LIST:
						#root_var.dict_value[loop_var_expr.var_expr_name]\
						#	= table_val.list_value[k]
						set_var(loop_var_expr.var_expr_name, table_val.list_value[k])

					loop_contents = block_eval(blocks[i+1:j])
					retval += loop_contents

				for k in range(i,j):
					#hack to skip past blocks evaluated in for loop
					blocks[k] = RawBlock(block_type=BlockTypes.RAW,\
						raw_block_value="", block_linenum=-1)

				retlist.append(retval)
				del_scope_frame()
				continue

			# the "output" tag evaluates its contents, and then outputs the result
			#	to the specified file

			if cur_stmt == "output":
				new_scope_frame()
				#TODO: error handling after everything

				output_arg = get_stmt_expr(block)
				output_path = expr_eval(output_arg)
				if not output_path.value_type == ValueTypes.STR:
					error("output requires a string", block)
				pathname = output_path.str_value

				# figure out the scope of this block
				# code stolen from the for loop code; hence "loop level"

				loop_level = 1
				j = i+1
				while j < len(blocks):
					inner_block = blocks[j]
					if is_raw(inner_block):
						j += 1
						continue
					inner_stmt = get_stmt(inner_block)
					if inner_stmt == "output":
						loop_level += 1
					if inner_stmt == "endoutput":
						# note: no error checking regarding format of endoutput stmt
						loop_level -= 1
					if loop_level == 0:
						break
					j += 1
				if not loop_level == 0:
					error("output tag isn't closed", block)

				# actually write to the file
				retval = block_eval(blocks[i+1:j])
				print(pathname)
				with open(pathname, "w") as fp:
					fp.write(retval)

				for k in range(i,j):
					#hack to skip past blocks evaluated in output statement
					blocks[k] = RawBlock(block_type=BlockTypes.RAW,\
						raw_block_value="", block_linenum=-1)
				del_scope_frame()
				continue

			if cur_stmt == "if":
				new_scope_frame()
				#TODO: error handling after everything

				if_expr = get_stmt_expr(block)

				# figure out the scope of this block
				# code stolen from the for loop code; hence "loop level"

				loop_level = 1
				j = i+1
				while j < len(blocks):
					inner_block = blocks[j]
					if is_raw(inner_block):
						j += 1
						continue
					inner_stmt = get_stmt(inner_block)
					if inner_stmt == "if":
						loop_level += 1
					if inner_stmt == "endif":
						# note: no error checking regarding format of endoutput stmt
						loop_level -= 1
					if loop_level == 0:
						break
					j += 1

				if not loop_level == 0:
					error("if statement isn't closed", block)

				result = expr_eval(if_expr)

				if result != NumValue(value_type=ValueTypes.NUM, num_value=0):
					# we follow the C convention that everything other than 0
					#	is true
					retlist.append(block_eval(blocks[i+1:j]))

				for k in range(i,j):
					#hack to skip past blocks evaluated in if statement
					blocks[k] = RawBlock(block_type=BlockTypes.RAW,\
						raw_block_value="", block_linenum=-1)
				del_scope_frame()
				continue
		except BastetError as e:
			print("Error in block",i)
			print("\t", blocks[i])
			print("-----------------")
			raise e

	return "".join(retlist)

def text_eval(text):
	return block_eval(blockify(text))

if __name__ == "__main__":
	if len(sys.argv) == 1:
		print("Usage: {sys.argv[0]} FILE_TO_READ")
	with open(sys.argv[1]) as fp:
		print(text_eval(fp.read()))
