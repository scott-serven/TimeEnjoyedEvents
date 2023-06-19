const feed = new EventSource('https://codejam.timeenjoyed.dev/api/teams/feed_event');


const langs = {
    0: 'No Preference',
    1: 'Python',
    2: 'JavaScript',
    3: 'TypeScript',
    4: 'Java',
    5: 'Kotlin',
    6: 'C++',
    7: 'C',
    8: 'C#',
    9: 'Rust',
    10: 'Go',
    11: 'Swift',
    12: 'Bash/Shell',
    13: 'Lua',
    14: 'VisualBasic',
    15: 'Haskell',
    16: 'Dart',
    17: 'PHP',
    18: 'Other...'
}

function showPopup(e, member) {
    const popup = document.querySelector('#memberInfoPopup');
    const languages = document.querySelector('#memberLanguages');
    const timezone = document.querySelector('#memberTimeZone');
    languages.innerHTML = `
        <ul>
        ${member['languages'].map((lang) => {
        return(`<li>${langs[lang]}</li>`)
    }).join('')}
        </ul>
    `
    timezone.innerHTML = `
        <span>GMT${member['timezone'] > 0 ? '+' : ''}${member['timezone']}</span>
    `
    const rect = e.target.getBoundingClientRect();
    const docRect = document.documentElement.getBoundingClientRect();

    // always reset since we might switch sides since last display
    popup.style.left = '';
    popup.style.right = '';
    popup.style.top = '';
    popup.style.bottom = '';

    // position popup so it fits on the screen
    if (rect.top > docRect.height / 2) {
        popup.style.bottom = (docRect.height - rect.y - rect.height) + 'px';
    } else {
        popup.style.top = rect.y + 'px';
    }

    if (rect.left > docRect.width / 2) {
        popup.style.right = (docRect.width - rect.x) + 25 + 'px';
    } else {
        popup.style.left = rect.x + rect.width + 25 + 'px';
    }

    popup.style.visibility = 'visible';
}

function closePopup(e) {
    const popup = document.querySelector('#memberInfoPopup');
    e.target.style.zIndex = '0';
    popup.style.visibility = 'hidden';
}

function formatMember(member) {
    return `
        <div class="teamMemberContainer">
            <img class="teamMemberImage" src="${member['avatar']}">
            <div class="teamMemberName">${member['name']}</div>
        </div>
    `;
}

function addMemberPopupEvents(memberContainer, member) {
    const memberHoverElement = memberContainer.querySelector('.teamMemberImage');
    memberHoverElement.addEventListener('click', (event) => {
        showPopup(event, member);
    });
    memberHoverElement.addEventListener('mouseenter', (event) => {
        showPopup(event, member);
    });
    memberHoverElement.addEventListener('mouseleave', (event) => {
        closePopup(event);
    });
}

function updateLookingForGroupData(data) {
    const MAX_TZ = 25; // not sure the range we allowed for signups, but we need an extra timezone for some reason
    const container = document.querySelector('.unassignedMembers');
    container.innerHTML = '';

    // The time zone blocks are so close together that if two people are in adjacent time zones, their names would
    // overlap if they were positioned right next to each other.  So we're going to calculate a vertical offset
    // to apply per column to get around the potential overlapping.
    let tzMemberMap = [];
    for (let x = 0; x < MAX_TZ; x++) {
        tzMemberMap.push([]);
    }

    for (let team in data) {
        if (team === "None") {
            const members = data[team];
            for (let member of members) {
                if (member['solo'] === false) {
                    member['top'] = tzMemberMap[member['timezone'] + 12].length;
                    tzMemberMap[member['timezone'] + 12].push(member);
                }
            }
        }
    }

    let tzVerticalOffsets = [0]; // first tz is always zero, and we start calculating at 2nd col in loop
    for (let x = 1; x < MAX_TZ; x++) {
        let offset = tzMemberMap[x-1].length;
        if ((offset > 0) && (x > 1)) {
            offset += tzMemberMap[x-2].length;
        }
        tzVerticalOffsets.push(offset);
    }

    for (let team in data) {
        const members = data[team];
        if (team === "None") {
            for (let member of members) {
                if (member['solo'] === false) {
                    let leftPos = (member['timezone'] + 12) * 4; // 4 is the 4% which is the width of each time zone (100 / 25)
                    let topPos = (tzVerticalOffsets[member['timezone'] + 12] * 90) + (member['top'] * 90) + 30; // all magic numbers
                    let memberContainer = document.createElement('div');
                    memberContainer.className = 'absMemberContainer';
                    memberContainer.style.left = `calc(${leftPos}%)`;
                    memberContainer.style.top = `${topPos}px`;
                    memberContainer.innerHTML = formatMember(member);
                    container.appendChild(memberContainer);
                    addMemberPopupEvents(memberContainer, member);
                }
            }
        }
    }
}

function updateTeamData(data) {
    const container = document.querySelector('.teamsInnerContainer');
    container.innerHTML = '';

    for (let team in data) {
        const members = data[team];

        if ((team !== "None") && (team !== "CodeJam Managers")) {
            // teams that consist of only one member that's a "solo" member, doesn't count as a team
            let allSoloTeam = members.reduce((acc, curr) => acc && curr['solo'], true);
            if (!allSoloTeam) {
                const teamDiv = document.createElement('div');
                teamDiv.className = 'teamContainer';
                teamDiv.insertAdjacentHTML('beforeend', `<header>${team}</header>`);
                for (let member of members) {
                    let memberContainer = document.createElement('div');
                    memberContainer.innerHTML = formatMember(member);
                    teamDiv.appendChild(memberContainer);
                    addMemberPopupEvents(memberContainer, member);
                }
                container.appendChild(teamDiv);
            }
        }
    }
}

function updateSoloData(data) {
    const container = document.querySelector('.soloInnerContainer');
    container.innerHTML = '';

    for (let team in data) {
        const members = data[team];

        if (team !== "CodeJam Managers") {
            let allSoloTeam = true;
            if (team !== "None") {
                allSoloTeam = members.reduce((acc, curr) => acc && curr['solo'], true);
            }
            if (allSoloTeam) {
                for (let member of members) {
                    if (member['solo'] === true) {
                        let memberContainer = document.createElement('div');
                        memberContainer.innerHTML = formatMember(member);
                        addMemberPopupEvents(memberContainer, member);
                        container.appendChild(memberContainer);
                    }
                }
            }
        }
    }
}

function updateCodeJamManagers(data) {
    const container = document.querySelector('footer');
    container.innerHTML = '<h3>CodeJam Managers</h3>';

    for (let team in data) {
        const members = data[team];

        if (team === "CodeJam Managers") {
            for (let member of members) {
                let memberContainer = document.createElement('div');
                memberContainer.innerHTML = formatMember(member);
                addMemberPopupEvents(memberContainer, member);
                container.appendChild(memberContainer);
            }
        }
    }
}

feed.onmessage = async (ev) => {
    const data = JSON.parse(ev.data);

    updateTeamData(data);
    updateLookingForGroupData(data);
    updateSoloData(data);
    updateCodeJamManagers(data);
}