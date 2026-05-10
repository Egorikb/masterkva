"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useAuthStore } from "@/lib/auth-store";
import { User, Bell, Volume2, Moon, Shield } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuthStore();

  if (!user) return null;

  return (
    <div className="p-6 lg:p-8">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold text-foreground lg:text-3xl">
          Настройки
        </h1>
        <p className="text-muted-foreground">
          Управляйте своим аккаунтом
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              Профиль
            </CardTitle>
            <CardDescription>
              Основная информация об аккаунте
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Имя</Label>
              <Input id="name" defaultValue={user.name} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" defaultValue={user.email} />
            </div>
            <Button className="w-full">Сохранить изменения</Button>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary" />
              Уведомления
            </CardTitle>
            <CardDescription>
              Настройки оповещений
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Напоминания об уроках</p>
                <p className="text-sm text-muted-foreground">
                  Получать напоминания о занятиях
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Достижения</p>
                <p className="text-sm text-muted-foreground">
                  Уведомлять о новых достижениях
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Email-отчёты</p>
                <p className="text-sm text-muted-foreground">
                  Еженедельные отчёты для родителей
                </p>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>

        {/* Sound & Display */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-primary" />
              Звук и отображение
            </CardTitle>
            <CardDescription>
              Настройки интерфейса
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Звуковые эффекты</p>
                <p className="text-sm text-muted-foreground">
                  Звуки при правильных ответах
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Голос Сенсея</p>
                <p className="text-sm text-muted-foreground">
                  Озвучивание ответов
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Moon className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="font-medium text-foreground">Тёмная тема</p>
                  <p className="text-sm text-muted-foreground">
                    Переключить на тёмный режим
                  </p>
                </div>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>

        {/* Privacy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              Конфиденциальность
            </CardTitle>
            <CardDescription>
              Безопасность и данные
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button variant="outline" className="w-full">
              Сменить пароль
            </Button>
            <Button variant="outline" className="w-full text-destructive hover:text-destructive">
              Удалить аккаунт
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
