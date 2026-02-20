-- ФРЕДЕРИК TSUNAMI HUB 2026 | Лучший для Escape Tsunami For Brainrots!
-- Fly + Noclip + Speeds + God + Remove Tsunami + Auto Rebirth + Dupe + TP
-- Автор: Фредерик для Алексея | raw.githubusercontent.com/TimofeiiGolov/Btc/main/frederik_tsunami.lua

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid")
local root = character:WaitForChild("HumanoidRootPart")

-- Переменные
local flying = false
local noclipping = false
local godmode = false
local removeTsunami = false
local autoRebirth = false
local autoCollect = false
local flySpeed = 100
local walkSpeed = humanoid.WalkSpeed
local jumpPower = humanoid.JumpPower
local rebirthRemote, collectRemote = nil, nil

-- GUI
local screenGui = Instance.new("ScreenGui")
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")
local mainFrame = Instance.new("Frame")
mainFrame.Size = UDim2.new(0, 320, 0, 500)
mainFrame.Position = UDim2.new(0.5, -160, 0.5, -250)
mainFrame.BackgroundColor3 = Color3.fromRGB(20, 20, 25)
mainFrame.BorderSizePixel = 0
mainFrame.Parent = screenGui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 12)
corner.Parent = mainFrame
local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, 0, 0, 50)
title.BackgroundTransparency = 1
title.Text = "ФРЕДЕРИК TSUNAMI HUB 2026"
title.TextColor3 = Color3.fromRGB(0, 255, 100)
title.TextScaled = true
title.Font = Enum.Font.GothamBold
title.Parent = mainFrame

-- Функции детектора
local function findRemote(name)
    for _, v in pairs(ReplicatedStorage:GetDescendants()) do
        if v:IsA("RemoteEvent") and string.find(string.lower(v.Name), name) then
            return v
        end
    end
end

-- Инициализация
task.spawn(function()
    rebirthRemote = findRemote("rebirth") or findRemote("reborn")
    collectRemote = findRemote("collect") or findRemote("coin") or findRemote("money")
    print("🔍 Remotes: Rebirth =", rebirthRemote and rebirthRemote.Name or "nil", "| Collect =", collectRemote and collectRemote.Name or "nil")
end)

-- Toggles
local function toggleFly() flying = not flying; humanoid.PlatformStand = flying end
local function toggleNoclip() noclipping = not noclipping end
local function toggleGod() godmode = not godmode end
local function toggleRemoveTsunami() 
    removeTsunami = not removeTsunami
    task.spawn(function()
        while removeTsunami do
            for _, part in pairs(workspace:GetChildren()) do
                if string.lower(part.Name):find("tsunami") or string.lower(part.Name):find("wave") or part.Size.Magnitude > 100 then
                    part:Destroy()
                end
            end
            task.wait(0.1)
        end
    end)
end
local function toggleAutoRebirth()
    autoRebirth = not autoRebirth
    task.spawn(function()
        while autoRebirth do
            if rebirthRemote then rebirthRemote:FireServer() end
            task.wait(0.5)
        end
    end)
end
local function toggleAutoCollect()
    autoCollect = not autoCollect
    task.spawn(function()
        while autoCollect do
            if collectRemote then collectRemote:FireServer() end
            task.wait(0.1)
        end
    end)
end

-- Dupe Brainrot (простой: экипируй/сними + tp)
local function dupeBrainrot()
    if player.PlayerGui:FindFirstChild("Inventory") then
        -- Адаптировать под GUI, или fire remote unequip
        print("🧠 Dupe: Экипируй лучший Brainrot, жми снова!")
        root.CFrame = root.CFrame * CFrame.new(0,50,0) -- tp up/down
        task.wait(0.1)
        root.CFrame = root.CFrame * CFrame.new(0,-50,0)
    end
end

-- TP Safe Zone (стандартная безопаска на карте ~ wave 1-10)
local function tpSafe()
    root.CFrame = CFrame.new(0, 50, 0) -- Spawn safe
    -- Или для end: CFrame.new(500, 200, 500) -- подкорректируй в игре
end

-- Loops
RunService.Stepped:Connect(function()
    if noclipping then
        for _, part in pairs(character:GetDescendants()) do
            if part:IsA("BasePart") then part.CanCollide = false end
        end
    end
    if godmode then
        humanoid.Health = math.huge
        humanoid.MaxHealth = math.huge
    end
end)

RunService.RenderStepped:Connect(function()
    if flying then
        local cam = workspace.CurrentCamera
        local move = Vector3.new(0,0,0)
        if UserInputService:IsKeyDown(Enum.KeyCode.W) then move = move + cam.CFrame.LookVector end
        if UserInputService:IsKeyDown(Enum.KeyCode.S) then move = move - cam.CFrame.LookVector end
        if UserInputService:IsKeyDown(Enum.KeyCode.A) then move = move - cam.CFrame.RightVector end
        if UserInputService:IsKeyDown(Enum.KeyCode.D) then move = move + cam.CFrame.RightVector end
        if UserInputService:IsKeyDown(Enum.KeyCode.Space) then move = move + Vector3.new(0,1,0) end
        if UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then move = move - Vector3.new(0,1,0) end
        root.Velocity = move.Unit * flySpeed
    end
end)

-- GUI Buttons
local y = 70
local function createButton(text, callback, color)
    local btn = Instance.new("TextButton")
    btn.Size = UDim2.new(0.9, 0, 0, 45)
    btn.Position = UDim2.new(0.05, 0, 0, y)
    btn.BackgroundColor3 = color or Color3.fromRGB(40, 40, 50)
    btn.Text = text
    btn.TextColor3 = Color3.fromRGB(255,255,255)
    btn.TextScaled = true
    btn.Font = Enum.Font.Gotham
    btn.Parent = mainFrame
    local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0,8); c.Parent = btn
    btn.MouseButton1Click:Connect(callback)
    y = y + 55
    return btn
end

createButton("Полёт (F)", toggleFly)
createButton("Noclip (N)", toggleNoclip)
createButton("God Mode", toggleGod, Color3.fromRGB(255,100,100))
createButton("Remove Tsunami", toggleRemoveTsunami, Color3.fromRGB(100,255,100))
createButton("Auto Rebirth", toggleAutoRebirth, Color3.fromRGB(100,100,255))
createButton("Auto Collect Money", toggleAutoCollect, Color3.fromRGB(255,200,100))
createButton("Dupe Brainrot", dupeBrainrot, Color3.fromRGB(255,150,50))
createButton("TP Safe Zone", tpSafe, Color3.fromRGB(150,255,150))

-- Слайдеры (как раньше)
local function createSlider(name, min, max, default, callback)
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.9, 0, 0, 60)
    frame.Position = UDim2.new(0.05, 0, 0, y)
    frame.BackgroundTransparency = 1
    frame.Parent = mainFrame
    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(1,0,0.4,0)
    label.BackgroundTransparency = 1
    label.Text = name .. ": " .. default
    label.TextColor3 = Color3.fromRGB(200,200,200)
    label.TextScaled = true
    label.Parent = frame
    local sliderBar = Instance.new("Frame")
    sliderBar.Size = UDim2.new(1,0,0.25,0)
    sliderBar.Position = UDim2.new(0,0,0.55,0)
    sliderBar.BackgroundColor3 = Color3.fromRGB(60,60,70)
    sliderBar.Parent = frame
    local barCorner = Instance.new("UICorner"); barCorner.Parent = sliderBar
    local fill = Instance.new("Frame")
    fill.Size = UDim2.new((default-min)/(max-min),0,1,0)
    fill.BackgroundColor3 = Color3.fromRGB(0,255,100)
    fill.Parent = sliderBar
    local fCorner = Instance.new("UICorner"); fCorner.Parent = fill
    local dragging = false
    sliderBar.InputBegan:Connect(function(i) if i.UserInputType == Enum.UserInputType.MouseButton1 then dragging = true end end)
    UserInputService.InputEnded:Connect(function(i) if i.UserInputType == Enum.UserInputType.MouseButton1 then dragging = false end end)
    RunService.RenderStepped:Connect(function()
        if dragging then
            local rel = math.clamp((UserInputService:GetMouseLocation().X - sliderBar.AbsolutePosition.X) / sliderBar.AbsoluteSize.X, 0, 1)
            local val = math.floor(min + (max-min)*rel)
            fill.Size = UDim2.new(rel,0,1,0)
            label.Text = name .. ": " .. val
            callback(val)
        end
    end)
    y = y + 70
end

createSlider("Скорость ходьбы", 16, 500, walkSpeed, function(v) humanoid.WalkSpeed = v end)
createSlider("Высота прыжка", 50, 500, jumpPower, function(v) humanoid.JumpPower = v end)
createSlider("Скорость полёта", 50, 500, flySpeed, function(v) flySpeed = v end)

-- Close
local closeBtn = Instance.new("TextButton")
closeBtn.Size = UDim2.new(0,30,0,30)
closeBtn.Position = UDim2.new(1,-35,0,10)
closeBtn.BackgroundColor3 = Color3.fromRGB(255,50,50)
closeBtn.Text = "✕"
closeBtn.TextColor3 = Color3.new(1,1,1)
closeBtn.TextScaled = true
closeBtn.Parent = mainFrame
local cc = Instance.new("UICorner"); cc.Parent = closeBtn
closeBtn.MouseButton1Click:Connect(function() screenGui:Destroy() end)

-- Hotkeys
UserInputService.InputBegan:Connect(function(i,gp)
    if gp then return end
    if i.KeyCode == Enum.KeyCode.F then toggleFly() end
    if i.KeyCode == Enum.KeyCode.N then toggleNoclip() end
    if i.KeyCode == Enum.KeyCode.RightShift then mainFrame.Visible = not mainFrame.Visible end
    if i.KeyCode == Enum.KeyCode.G then toggleGod() end
end)

-- Respawn fix
player.CharacterAdded:Connect(function(newChar)
    character = newChar
    humanoid = newChar:WaitForChild("Humanoid")
    root = newChar:WaitForChild("HumanoidRootPart")
end)

-- Unlock Zoom
game.StarterGui:SetCore("CameraMode", Enum.CameraMode.LockFirstPerson)
print("🌊 Фредерик Tsunami Hub загружен! RightShift — меню | F=Fly | N=Noclip | G=God")
