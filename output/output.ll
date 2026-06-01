; ModuleID = "TinyStack"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"main"()
{
entry:
  %"x_ptr" = alloca i32
  store i32 20, i32* %"x_ptr"
  %"x_value" = load i32, i32* %"x_ptr"
  %"add_result" = add i32 %"x_value", 10
  %"mul_result" = mul i32 %"add_result", 2
  %"sub_result" = sub i32 %"mul_result", 5
  %".3" = bitcast [12 x i8]* @"fmt_1" to i8*
  %".4" = call i32 (i8*, ...) @"printf"(i8* %".3", i32 %"sub_result")
  ret i32 0
}

declare i32 @"printf"(i8* %".1", ...)

@"fmt_1" = constant [12 x i8] c"Result: %d\0a\00"