; ModuleID = "TinyStack_Op!="
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"main"()
{
entry:
  %"x_ptr" = alloca i32
  store i32 1, i32* %"x_ptr"
  %"cmp_ne" = icmp ne i32 1, 2
  br i1 %"cmp_ne", label %"if_then_1", label %"if_else_1"
if_then_1:
  store i32 1, i32* %"x_ptr"
  br label %"if_end_1"
if_else_1:
  store i32 0, i32* %"x_ptr"
  br label %"if_end_1"
if_end_1:
  ret i32 0
}

declare i32 @"printf"(i8* %".1", ...)
