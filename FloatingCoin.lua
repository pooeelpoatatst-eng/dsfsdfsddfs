-- Floating Coin
-- Вставь этот скрипт в Workspace как обычный Script (ServerScript)

local TweenService = game:GetService("TweenService")

local COIN_START = Vector3.new(0, 5, 0) -- высота, где парит монета
local FLOAT_HEIGHT = 1.5                -- амплитуда покачивания (вверх/вниз)
local FLOAT_TIME = 2                      -- время одного цикла

-- Создаём монету
local coin = Instance.new("Part")
coin.Name = "FloatingCoin"
coin.Shape = Enum.PartType.Cylinder
coin.Size = Vector3.new(0.4, 2, 2)        -- тонкий цилиндр = монета
coin.BrickColor = BrickColor.new("Bright yellow") -- золотой цвет
coin.Material = Enum.Material.Metal
coin.Anchored = true
coin.CanCollide = false
coin.Orientation = Vector3.new(0, 0, 90)  -- поставить "плашмя"
coin.Position = COIN_START
coin.Parent = workspace

-- Эффект свечения (необязательно)
local glow = Instance.new("PointLight")
glow.Color = Color3.fromRGB(255, 215, 0)
glow.Range = 8
glow.Brightness = 1
glow.Parent = coin

-- Плавное парение вверх-вниз через Tween
local upGoal = {Position = COIN_START + Vector3.new(0, FLOAT_HEIGHT, 0)}
local downGoal = {Position = COIN_START - Vector3.new(0, FLOAT_HEIGHT, 0)}

local upTween = TweenService:Create(coin, TweenInfo.new(FLOAT_TIME, Enum.EasingStyle.Sine, Enum.EasingDirection.Out, -1, true), upGoal)
upTween:Play()
upTween.Completed:Connect(function()
	local downTween = TweenService:Create(coin, TweenInfo.new(FLOAT_TIME, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), downGoal)
	downTween:Play()
end)

-- Медленное вращение вокруг своей оси
game:GetService("RunService").Heartbeat:Connect(function(dt)
	coin.CFrame = coin.CFrame * CFrame.Angles(0, math.rad(60) * dt, 0)
end)
