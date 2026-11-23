--[[
    Dialogue helpers for The Dreamlands.

    tdl_roll: a random 0-3 that dialogue filters use to vary responses
    (see dialogue/states.yaml). Re-rolled when a conversation opens and after
    every response, so asking the same NPC for rumours again can give a new one.
]]
local this = {}

local function reroll()
    local roll = tes3.findGlobal("tdl_roll")
    if roll then
        roll.value = math.random(0, 3)
    end
end

function this.init()
    event.register(tes3.event.uiActivated, reroll, { filter = "MenuDialog" })
    event.register(tes3.event.infoResponse, reroll)
end

return this
