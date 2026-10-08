-- anonymize.lua — drop the author block for the double-blind review copy.
--
-- The author lines in 00_frontmatter.md sit inside a fenced div of class
-- "author".  Normally the div is transparent (its paragraphs render as they
-- are).  When pandoc is run with  -M anonymous=true  every such div is removed,
-- so the name, affiliation and e-mail never reach the output.
--
-- Used by build.ps1 / preview.ps1 via their -Anonymous switch.

local anonymous = false

local function read_meta(m)
  local v = m.anonymous
  if v ~= nil then
    local s = pandoc.utils.stringify(v)
    anonymous = (s == 'true' or s == 'yes' or s == '1')
  end
  return m
end

local function author_div(el)
  if not el.classes:includes('author') then return nil end
  if anonymous then return {} end
  return el.content
end

-- Meta must be seen before the body is walked: pandoc runs the returned
-- filter tables in order.
return { { Meta = read_meta }, { Div = author_div } }
