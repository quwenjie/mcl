import sys
import argparse

def gen_func(name, ret, args, cname, params, i, asPointer=False):
	retstr = '' if ret == 'void' else ' return'
	if asPointer:
		print('#ifdef MCL_BINT_FUNC_PTR')
		print(f'extern "C" {ret} (*{cname}{i})({args});')
		print(f'extern "C" {ret} {cname}{i}_slow({args});')
		print(f'extern "C" {ret} {cname}{i}_fast({args});')
		print('#else')
		print(f'extern "C" {ret} {cname}{i}({args});')
		print('#endif')
	else:
		print(f'extern "C" {ret} {cname}{i}({args});')
	print(f'template<> inline {ret} {name}<{i}>({args}) {{{retstr} {cname}{i}({params}); }}')

def gen_switch(name, ret, args, cname, params, N, N64):
	ret0 = 'return' if ret == 'void' else 'return 0'
	print(f'''{ret} {name}({args}, size_t n)
{{
	switch (n) {{
	default: assert(0); {ret0};''')
	for i in range(1, N):
		if i == N64 + 1:
			print('#if MCL_SIZEOF_UNIT == 4')
		call = f'{cname}<{i}>({params})'
		if ret == 'void':
			print(f'\tcase {i}: {call}; return;')
		else:
			print(f'\tcase {i}: return {call};')
	print('#endif\n\t}\n}')

def gen_inst(name, ret, args, N, N64):
	for i in range(1, N):
		if i == N64 + 1:
			print('#if MCL_SIZEOF_UNIT == 4')
		print(f'template {ret} {name}<{i}>({args});')
	print('#endif')

arg_p3 = 'Unit *z, const Unit *x, const Unit *y'
arg_p2u = 'Unit *z, const Unit *x, Unit y'
param_u3 = 'z, x, y'

def roundup(x, n):
	return (x + n - 1) // n

def main():
	parser = argparse.ArgumentParser(description='gen header')
	parser.add_argument('out', type=str)
	parser.add_argument('-max_bit', type=int, default=512+32)
	opt = parser.parse_args()
	if not opt.out in ['asm', 'switch']:
		print('bad out', opt.out)
		sys.exit(1)
	N = roundup(opt.max_bit, 32)
	N64 = roundup(opt.max_bit, 64)
	addN = 32
	addN64 = 16

	print('// this code is generated by python3 src/gen_bint_header.py', opt.out)
	if opt.out == 'asm':
		print('''#if (CYBOZU_HOST == CYBOZU_HOST_INTEL) && (MCL_SIZEOF_UNIT == 8)
	#define MCL_BINT_FUNC_PTR
extern "C" void mclb_enable_fast(void);
#endif''')
		for i in range(1, addN+1):
			if i == addN64 + 1:
				print('#if MCL_SIZEOF_UNIT == 4')
			gen_func('addT', 'Unit', arg_p3, 'mclb_add', param_u3, i)
			gen_func('subT', 'Unit', arg_p3, 'mclb_sub', param_u3, i)
		print('#endif')
		for i in range(1, N+1):
			if i == N64 + 1:
				print('#if MCL_SIZEOF_UNIT == 4')
			gen_func('mulUnitT', 'Unit', arg_p2u, 'mclb_mulUnit', param_u3, i, True)
			gen_func('mulUnitAddT', 'Unit', arg_p2u, 'mclb_mulUnitAdd', param_u3, i, True)
		print('#endif')
	elif opt.out == 'switch':
		gen_switch('addN', 'Unit', arg_p3, 'addT', param_u3, addN, addN64)
		gen_switch('subN', 'Unit', arg_p3, 'subT', param_u3, addN, addN64)
		gen_switch('mulUnitN', 'Unit', arg_p2u, 'mulUnitT', param_u3, N, N64)
		gen_switch('mulUnitAddN', 'Unit', arg_p2u, 'mulUnitAddT', param_u3, N, N64)
		gen_switch('mulN', 'void', arg_p3, 'mulT', param_u3, N, N64)
		print('#if MCL_BINT_ASM != 1')
		gen_inst('addT', 'Unit', arg_p3, addN, addN64)
		gen_inst('subT', 'Unit', arg_p3, addN, addN64)
		gen_inst('mulUnitT', 'Unit', arg_p2u, N, N64)
		gen_inst('mulUnitAddT', 'Unit', arg_p2u, N, N64)
		print('#endif')
	else:
		print('err : bad out', out)

main()

