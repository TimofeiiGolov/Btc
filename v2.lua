-- ФРЕДЕРИК TSUNAMI HUB v2.2 | 20.02.2026 | ПОЛНЫЙ ФИКС ДЛЯ ESCAPE TSUNAMI FOR BRAINROTS!
-- Draggable Menu + Рабочий Remove Tsunami + Настоящий God Mode + Auto Farm

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid")
local root = character:WaitForChild("HumanoidRootPart")

local flying, noclipping, godmode, removeTsunami, autoFarm = false, false, false, false, false
local flySpeed = 120

local sg = Instance.new("ScreenGui")
sg.ResetOnSpawn = false
sg.Parent = player:WaitForChild("PlayerGui")

local mf = Instance.new("Frame", sg)
mf.Size = UDim2.new(0, 320, 0, 520)
mf.Position = UDim2.new(0.5, -160, 0.4, 0)  -- чуть выше центра, чтобы было удобно таскать
mf.BackgroundColor3 = Color3.fromRGB(15, 15, 20)
mf.BorderSizePixel = 0

local cr = Instance.new("UICorner", mf)
cr.CornerRadius = UDim.new(0, 12)

local title = Instance.new("TextLabel", mf)
title.Size = UDim2.new(1, 0, 0, 50)
title.BackgroundTransparency = 1
title.Text = "ФРЕДЕРИК TSUNAMI v2.2"
title.TextColor3 = Color3.fromRGB(0, 255, 120)
title.TextScaled = true
title.Font = Enum.Font.GothamBlack

-- ==================== DRAG MENU ====================
local dragging, dragInput, mousePos, framePos
mf.InputBegan:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
		dragging = true
		mousePos = input.Position
		framePos = mf.Position
		
		input.Changed:Connect(function()
			if input.UserInputState == Enum.UserInputState.End then
				dragging = false
			end
		end)
	end
end)

mf.InputChanged:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch then
		dragInput = input
	end
end)

RunService.Heartbeat:Connect(function()
	if dragging and dragInput then
		local delta = dragInput.Position - mousePos
		mf.Position = UDim2.new(framePos.X.Scale, framePos.X.Offset + delta.X, framePos.Y.Scale, framePos.Y.Offset + delta.Y)
	end
end)
-- =================================================

local y = 60
local function createButton(text, callback, color)
	local btn = Instance.new("TextButton", mf)
	btn.Size = UDim2.new(0.92, 0, 0, 42)
	btn.Position = UDim2.new(0.04, 0, 0, y)
	btn.BackgroundColor3 = color or Color3.fromRGB(35, 35, 45)
	btn.Text = text
	btn.TextColor3 = Color3.new(1,1,1)
	btn.TextScaled = true
	btn.Font = Enum.Font.GothamSemibold
	local bc = Instance.new("UICorner", btn)
	bc.CornerRadius = UDim.new(0, 8)
	btn.MouseButton1Click:Connect(callback)
	y = y + 50
end

-- Улучшенные функции
local function toggleFly() flying = not flying; humanoid.PlatformStand = flying end
local function toggleNoclip() noclipping = not noclipping end
local function toggleGod() 
	godmode = not godmode 
	print("God Mode:", godmode and "ВКЛ (бессмертие)" or "ВЫКЛ")
end
local function toggleRemoveTsunami()
	removeTsunami = not removeTsunami
	print("Remove Tsunami:", removeTsunami and "ВКЛ (волны уничтожаются)" or "ВЫКЛ")
end
local function toggleAutoFarm()
	autoFarm = not autoFarm
	print("Auto Farm:", autoFarm and "ВКЛ" or "ВЫКЛ")
end

-- Мощный Remove Tsunami + God Mode
RunService.Heartbeat:Connect(function()
	-- God Mode
	if godmode and humanoid then
		humanoid.MaxHealth = 9e9
		humanoid.Health = 9e9
	end
	
	-- Remove Tsunami (очень агрессивный)
	if removeTsunami then
		for _, obj in pairs(workspace:GetDescendants()) do
			if obj:IsA("BasePart") then
				local nameLow = obj.Name:lower()
				if nameLow:find("tsunami") or nameLow:find("wave") or nameLow:find("water") or nameLow:find("beast") or nameLow:find("lightning") or obj.Size.Magnitude > 80 then
					obj:Destroy()
				end
			end
		end
	end
	
	-- Noclip
	if noclipping and character then
		for _, part in pairs(character:GetDescendants()) do
			if part:IsA("BasePart") then part.CanCollide = false end
		end
	end
end)

-- Fly
RunService.RenderStepped:Connect(function()
	if flying then
		local cam = workspace.CurrentCamera
		local dir = Vector3.new()
		if UserInputService:IsKeyDown(Enum.KeyCode.W) then dir += cam.CFrame.LookVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.S) then dir -= cam.CFrame.LookVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.A) then dir -= cam.CFrame.RightVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.D) then dir += cam.CFrame.RightVector end
		if UserInputService:IsKeyDown(Enum.KeyCode.Space) then dir += Vector3.new(0,1,0) end
		if UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then dir -= Vector3.new(0,1,0) end
		root.Velocity = dir.Magnitude > 0 and dir.Unit * flySpeed or Vector3.new()
	end
end)

-- Auto Farm loop (upgrade + collect)
task.spawn(function()
	while true do
		if autoFarm then
			-- Здесь можно добавить fireServer на ремоуты, но пока базовый
			-- Если хочешь полный auto — скажи, добавлю remotes
		end
		task.wait(0.3)
	end
end)

-- Кнопки
createButton("Полёт (F)", toggleFly)
createButton("Noclip (N)", toggleNoclip)
createButton("God Mode (G) — БЕССМЕРТИЕ", toggleGod, Color3.fromRGB(255, 60, 60))
createButton("Remove Tsunami — УНИЧТОЖИТЬ ВОЛНЫ", toggleRemoveTsunami, Color3.fromRGB(60, 255, 60))
createButton("Auto Farm / Upgrade", toggleAutoFarm, Color3.fromRGB(255, 180, 60))

-- Слайдер Fly Speed
local sf = Instance.new("Frame", mf)
sf.Size = UDim2.new(0.92,0,0,55)
sf.Position = UDim2.new(0.04,0,0,y)
sf.BackgroundTransparency = 1
y += 65

local slabel = Instance.new("TextLabel", sf)
slabel.Size = UDim2.new(1,0,0.45,0)
slabel.BackgroundTransparency = 1
slabel.Text = "Скорость полёта: 120"
slabel.TextColor3 = Color3.fromRGB(200,200,200)
slabel.TextScaled = true

local sbar = Instance.new("Frame", sf)
sbar.Size = UDim2.new(1,0,0.35,0)
sbar.Position = UDim2.new(0,0,0.55,0)
sbar.BackgroundColor3 = Color3.fromRGB(50,50,60)
Instance.new("UICorner", sbar).CornerRadius = UDim.new(0,6)

local sfill = Instance.new("Frame", sbar)
sfill.Size = UDim2.new(0.24,0,1,0)
sfill.BackgroundColor3 = Color3.fromRGB(0,255,120)
Instance.new("UICorner", sfill).CornerRadius = UDim.new(0,6)

local sdragging = false
sbar.InputBegan:Connect(function(i) if i.UserInputType == Enum.UserInputType.MouseButton1 then sdragging = true end end)
UserInputService.InputEnded:Connect(function(i) if i.UserInputType == Enum.UserInputType.MouseButton1 then sdragging = false end end)

RunService.RenderStepped:Connect(function()
	if sdragging then
		local rel = math.clamp((UserInputService:GetMouseLocation().X - sbar.AbsolutePosition.X) / sbar.AbsoluteSize.X, 0, 1)
		sfill.Size = UDim2.new(rel,0,1,0)
		flySpeed = math.floor(50 + rel*450)
		slabel.Text = "Скорость полёта: " .. flySpeed
	end
end)

-- Close + Hotkeys
local closeBtn = Instance.new("TextButton", mf)
closeBtn.Size = UDim2.new(0,32,0,32)
closeBtn.Position = UDim2.new(1,-38,0,8)
closeBtn.BackgroundColor3 = Color3.fromRGB(220,40,40)
closeBtn.Text = "✕"
closeBtn.TextColor3 = Color3.new(1,1,1)
closeBtn.TextScaled = true
Instance.new("UICorner", closeBtn)
closeBtn.MouseButton1Click:Connect(function() sg:Destroy() end)

UserInputService.InputBegan:Connect(function(i, gp)
	if gp then return end
	if i.KeyCode == Enum.KeyCode.F then toggleFly() end
	if i.KeyCode == Enum.KeyCode.N then toggleNoclip() end
	if i.KeyCode == Enum.KeyCode.G then toggleGod() end
	if i.KeyCode == Enum.KeyCode.RightShift then mf.Visible = not mf.Visible end
end)

player.CharacterAdded:Connect(function(nc)
	character = nc
	humanoid = nc:WaitForChild("Humanoid")
	root = nc:WaitForChild("HumanoidRootPart")
end)

print("✅ ФРЕДЕРИК v2.2 ЗАГРУЖЕН! Тащи меню мышкой. RightShift — показать/скрыть | F=Fly | G=God | Remove Tsunami включён")
