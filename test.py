#   Copyright 2013 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2013 Red Hat, Inc.
#
#   This is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see
#   <http://www.gnu.org/licenses/>.

import unittest

import gccjit

class JitTests(unittest.TestCase):
    def test_square(self):
        def cb(ctxt):
            """
            Create this function:
              int square(int i)
              {
                 return i * i;
              }
            """
            param_i = ctxt.new_param(ctxt.get_type(gccjit.TYPE_INT),
                                     b'i')
            fn = ctxt.new_function(gccjit.FUNCTION_EXPORTED,
                                   ctxt.get_type(gccjit.TYPE_INT),
                                   b"square",
                                   [param_i])
            fn.add_return(ctxt.new_binary_op(gccjit.BINARY_OP_MULT,
                                             ctxt.get_type(gccjit.TYPE_INT),
                                             param_i, param_i))

        for i in range(5):
            ctxt = gccjit.Context(cb)
            if 0:
                ctxt.set_bool_option(gccjit.BOOL_OPTION_DUMP_INITIAL_TREE, True)
                ctxt.set_bool_option(gccjit.BOOL_OPTION_DUMP_INITIAL_GIMPLE, True)
            if 0:
                ctxt.set_int_option(gccjit.INT_OPTION_OPTIMIZATION_LEVEL, 0)
            result = ctxt.compile()
            code = result.get_code(b"square")
            self.assertEqual(code(5), 25)

    def test_sum_of_squares(self):
        def cb(ctxt):
            """
            Create this function:
              int loop_test (int n)
              {
                int i;
                int sum = 0;
                for (i = 0; i < n ; i ++)
                {
                  sum += i * i;
                }
                return sum;
              }
            """
            the_type = ctxt.get_type(gccjit.TYPE_INT)
            return_type = the_type
            param_n = ctxt.new_param(the_type, b"n")
            fn = ctxt.new_function(gccjit.FUNCTION_EXPORTED,
                                   return_type,
                                   b"loop_test",
                                   [param_n])
            # Build locals
            local_i = fn.new_local(the_type, b"i")
            local_sum = fn.new_local(the_type, b"sum")

            # Create forward label
            label_after_loop = fn.new_forward_label(b"after_loop")

            # sum = 0
            fn.add_assignment(local_sum, ctxt.zero(the_type))

            # i = 0
            fn.add_assignment(local_i, ctxt.zero(the_type))

            # label "cond:"
            label_cond = fn.add_label(b"cond")

            # if (i >= n)
            fn.add_conditional(ctxt.new_comparison(gccjit.COMPARISON_GE,
                                                   local_i, param_n),
                               label_after_loop)

            # sum += i * i
            fn.add_assignment_op(local_sum,
                                 gccjit.BINARY_OP_PLUS,
                                 ctxt.new_binary_op(gccjit.BINARY_OP_MULT,
                                                    the_type,
                                                    local_i, local_i))

            # i++
            fn.add_assignment_op(local_i,
                                 gccjit.BINARY_OP_PLUS,
                                 ctxt.one(the_type))

            # goto label_cond
            fn.add_jump(label_cond)

            # label "after_loop:"
            fn.place_forward_label(label_after_loop)

            # return sum
            fn.add_return(local_sum)

        for i in range(5):
            ctxt = gccjit.Context(cb)
            if 0:
                ctxt.set_bool_option(gccjit.BOOL_OPTION_DUMP_INITIAL_TREE, True)
                ctxt.set_bool_option(gccjit.BOOL_OPTION_DUMP_INITIAL_GIMPLE, True)
                ctxt.set_bool_option(gccjit.BOOL_OPTION_DUMP_EVERYTHING, True)
                ctxt.set_bool_option(gccjit.BOOL_OPTION_KEEP_INTERMEDIATES, True)
            if 0:
                ctxt.set_int_option(gccjit.INT_OPTION_OPTIMIZATION_LEVEL, 3)
            result = ctxt.compile()
            code = result.get_code(b"loop_test")
            self.assertEqual(code(10), 285)

if __name__ == '__main__':
    unittest.main()
