; ModuleID = '<string>'
source_filename = "<string>"
target triple = "x86_64-unknown-linux-gnu"

@fmt_1 = constant [12 x i8] c"Result: %d\0A\00"

define i32 @main() {
entry:
  %.4 = call i32 (ptr, ...) @printf(ptr noundef nonnull dereferenceable(1) @fmt_1, i32 55)
  ret i32 0
}

declare i32 @printf(ptr, ...)
