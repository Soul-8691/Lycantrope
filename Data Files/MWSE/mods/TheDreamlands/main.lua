--[[
    The Dreamlands: MWSE entry point. Each system lives in its own module
    (THE_DREAMLANDS.md §5) and registers its own events from init().
]]
local dialogue = require("TheDreamlands.dialogue")

event.register(tes3.event.initialized, function()
    dialogue.init()
    mwse.log("[The Dreamlands] initialized")
end)
