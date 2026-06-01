; ModuleID = "TinyStack_Print"
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"main"()
{
entry:
  %"x_ptr" = alloca i32
  store i32 42, i32* %"x_ptr"
  %"y_ptr" = alloca i32
  store i32 10, i32* %"y_ptr"
  %"x_value" = load i32, i32* %"x_ptr"
  %".4" = bitcast [4 x i8]* @"fmt_1" to i8*
  %".5" = call i32 (i8*, ...) @"printf"(i8* %".4", i32 %"x_value")
  %"y_value" = load i32, i32* %"y_ptr"
  %".6" = bitcast [4 x i8]* @"fmt_2" to i8*
  %".7" = call i32 (i8*, ...) @"printf"(i8* %".6", i32 %"y_value")
  %"add_result" = add i32 100, 50
  %".8" = bitcast [4 x i8]* @"fmt_3" to i8*
  %".9" = call i32 (i8*, ...) @"printf"(i8* %".8", i32 %"add_result")
  %"x_value.1" = load i32, i32* %"x_ptr"
  %"sub_result" = sub i32 %"x_value.1", 5
  %".10" = bitcast [4 x i8]* @"fmt_4" to i8*
  %".11" = call i32 (i8*, ...) @"printf"(i8* %".10", i32 %"sub_result")
  ret i32 0
}

declare i32 @"printf"(i8* %".1", ...)

@"fmt_1" = constant [4 x i8] c"%d\0a\00"
@"fmt_2" = constant [4 x i8] c"%d\0a\00"
@"fmt_3" = constant [4 x i8] c"%d\0a\00"
@"fmt_4" = constant [4 x i8] c"%d\0a\00"