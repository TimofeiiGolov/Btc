-- ФРЕДЕРИК УНИВЕРСАЛ 2027 | fly + noclip + speeds + меню
-- Автор: Фредерик для Алексея (последний выживший)

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid")
local root = character:WaitForChild("HumanoidRootPart")

local flying = false
local noclipping = false
local flySpeed = 100
local walkSpeed = humanoid.WalkSpeed
local jumpPower = humanoid.JumpPower

local screenGui = Instance.new("ScreenGui")
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

local mainFrame = Instance.new("Frame")
mainFrame.Size = UDim2.new(0, 280, 0, 420)
mainFrame.Position = UDim2.new(0.5, -140, 0.5, -210)
mainFrame.BackgroundColor3 = Color3.fromRGB(20, 20, 25)
mainFrame.BorderSizePixel = 0
mainFrame.Parent = screenGui

local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 12)
corner.Parent = mainFrame

local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, 0, 0, 50)
title.BackgroundTransparency = 1
title.Text = "ФРЕДЕРИК УНИВЕРСАЛ 2027"
title.TextColor3 = Color3.fromRGB(0, 255, 100)
title.TextScaled = true
title.Font = Enum.Font.GothamBold
title.Parent = mainFrame

local y = 70
local function createButton(text, callback)
	local btn = Instance.new("TextButton")
	btn.Size = UDim2.new(0.9, 0, 0, 45)
	btn.Position = UDim2.new(0.05, 0, 0, y)
	btn.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
	btn.Text = text
	btn.TextColor3 = Color3.fromRGB(255,255,255)
	btn.TextScaled = true
	btn.Font = Enum.Font.Gotham
	btn.Parent = mainFrame
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0,8); c.Parent = btn
	btn.MouseButton1Click:Connect(callback)
	y += 55
end

local function toggleFly()
	flying = not flying
	if flying then humanoid.PlatformStand = true else humanoid.PlatformStand = false end
end

local function toggleNoclip()
	noclipping = not noclipping
end

RunService.Stepped:Connect(function()
	if noclipping and character then
		for _, v in pairs(character:GetDescendants()) do
			if v:IsA("BasePart") then v.CanCollide = false end
		end
	end
end)

RunService.RenderStepped:Connect(function()
	if not flying then return end
	local cam = workspace.CurrentCamera
	local move = Vector3.new()
	if UserInputService:IsKeyDown(Enum.KeyCode.W) then move += cam.CFrame.LookVector end
	if UserInputService:IsKeyDown(Enum.KeyCode.S) then move -= cam.CFrame.LookVector end
	if UserInputService:IsKeyDown(Enum.KeyCode.A) then move -= cam.CFrame.RightVector end
	if UserInputService:IsKeyDown(Enum.KeyCode.D) then move += cam.CFrame.RightVector end
	if UserInputService:IsKeyDown(Enum.KeyCode.Space) then move += Vector3.new(0,1,0) end
	if UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then move -= Vector3.new(0,1,0) end
	if UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) then flySpeed = math.clamp(flySpeed + 5, 50, 500) end
	root.Velocity = move.Magnitude > 0 and move.Unit * flySpeed or Vector3.new()
end)

createButton("Полёт (F)", toggleFly)
createButton("Noclip (N)", toggleNoclip)

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
	y += 70
end

createSlider("Скорость ходьбы", 16, 300, walkSpeed, function(v) humanoid.WalkSpeed = v end)
createSlider("Высота прыжка", 50, 500, jumpPower, function(v) humanoid.JumpPower = v end)
createSlider("Скорость полёта", 50, 500, flySpeed, function(v) flySpeed = v end)

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

UserInputService.InputBegan:Connect(function(i,gp)
	if gp then return end
	if i.KeyCode == Enum.KeyCode.F then toggleFly() end
	if i.KeyCode == Enum.KeyCode.N then toggleNoclip() end
	if i.KeyCode == Enum.KeyCode.RightShift then mainFrame.Visible = not mainFrame.Visible end
end)

print("✅ Фредерик Универсал 2027 загружен. RightShift — меню")
