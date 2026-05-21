"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { useAuthStore, type UserRole } from "@/lib/auth-store";
import { Zap, Eye, EyeOff, ArrowLeft, GraduationCap, Users } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuthStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<UserRole>("student");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Пароли не совпадают");
      return;
    }

    if (password.length < 6) {
      setError("Пароль должен быть не менее 6 символов");
      return;
    }

    setIsLoading(true);

    try {
      const success = await signup(email, password, name, role);
      if (success) {
        router.push("/dashboard");
      } else {
        setError("Не удалось создать аккаунт");
      }
    } catch {
      setError("Произошла ошибка. Попробуйте ещё раз.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Background pattern */}
      <div className="fixed inset-0 -z-10 opacity-5">
        <div className="absolute left-0 top-0 h-full w-16 bg-gradient-to-r from-primary to-transparent" />
        <div className="absolute left-20 top-0 h-full w-8 bg-gradient-to-r from-primary/50 to-transparent" />
        <div className="absolute right-0 top-0 h-full w-16 bg-gradient-to-l from-primary to-transparent" />
        <div className="absolute right-20 top-0 h-full w-8 bg-gradient-to-l from-primary/50 to-transparent" />
      </div>

      {/* Back button */}
      <div className="p-4">
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            На главную
          </Button>
        </Link>
      </div>

      <main className="flex flex-1 items-center justify-center p-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <Card className="border-border/50 shadow-xl">
            <CardHeader className="space-y-4 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-jade-dark shadow-lg">
                <Zap className="h-7 w-7 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold text-foreground">
                  Начни путь мастера
                </CardTitle>
                <p className="mt-2 text-muted-foreground">
                  Создайте аккаунт и начните обучение
                </p>
              </div>
            </CardHeader>
            <CardContent>
              {/* Role Selector */}
              <div className="mb-6">
                <Label className="mb-3 block">Я регистрируюсь как:</Label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setRole("student")}
                    className={cn(
                      "flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all",
                      role === "student"
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <div className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full",
                      role === "student" ? "bg-primary text-white" : "bg-muted text-muted-foreground"
                    )}>
                      <GraduationCap className="h-5 w-5" />
                    </div>
                    <span className={cn(
                      "text-sm font-medium",
                      role === "student" ? "text-primary" : "text-foreground"
                    )}>
                      Ученик
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole("parent")}
                    className={cn(
                      "flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all",
                      role === "parent"
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <div className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full",
                      role === "parent" ? "bg-primary text-white" : "bg-muted text-muted-foreground"
                    )}>
                      <Users className="h-5 w-5" />
                    </div>
                    <span className={cn(
                      "text-sm font-medium",
                      role === "parent" ? "text-primary" : "text-foreground"
                    )}>
                      Родитель
                    </span>
                  </button>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    {role === "student" ? "Как тебя зовут?" : "Ваше имя"}
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder={role === "student" ? "Напиши своё имя" : "Введите имя"}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="h-11"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-11"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Пароль</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Минимум 6 символов"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="h-11 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? (
                        <EyeOff className="h-5 w-5" />
                      ) : (
                        <Eye className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Подтвердите пароль</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Повторите пароль"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="h-11"
                  />
                </div>

                {error && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-sm text-destructive"
                  >
                    {error}
                  </motion.p>
                )}

                <Button 
                  type="submit" 
                  className="h-11 w-full bg-primary hover:bg-primary/90"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Создаём аккаунт...
                    </>
                  ) : (
                    "Создать аккаунт"
                  )}
                </Button>
              </form>

              <div className="mt-6 text-center text-sm text-muted-foreground">
                Уже есть аккаунт?{" "}
                <Link href="/login" className="font-medium text-primary hover:underline">
                  Войти
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Fun message */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 text-center text-sm text-muted-foreground"
          >
            {role === "student" 
              ? "Готов стать настоящим мастером математики?" 
              : "Следите за успехами вашего ребёнка"}
          </motion.p>
        </motion.div>
      </main>
    </div>
  );
}
