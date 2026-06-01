; ModuleID = "TinyStack_PrintConditional"
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"main"()
{
entry:
  %"result_ptr" = alloca i32
  store i32 0, i32* %"result_ptr"
  %"cmp_gt" = icmp sgt i32 100, 50
  br i1 %"cmp_gt", label %"if_then_1", label %"if_else_1"
if_then_1:
  %".4" = bitcast [4 x i8]* @"fmt_1" to i8*
  %".5" = call i32 (i8*, ...) @"printf"(i8* %".4", i32 1)
  br label %"if_end_1"
if_else_1:
  %".7" = bitcast [4 x i8]* @"fmt_2" to i8*
  %".8" = call i32 (i8*, ...) @"printf"(i8* %".7", i32 0)
  br label %"if_end_1"
if_end_1:
  ret i32 0
}

declare i32 @"printf"(i8* %".1", ...)

@"fmt_1" = constant [4 x i8] c"%d\0a\00"
@"fmt_2" = constant [4 x i8] c"%d\0a\00"